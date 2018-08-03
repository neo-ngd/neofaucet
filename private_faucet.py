import os
import threading
import getpass
import logging
from time import sleep
from logzero import logger

from twisted.internet import reactor, task, endpoints
from twisted.web.server import Request, Site
from klein import Klein, resource

from neocore.Cryptography.Crypto import Crypto
from neo.SmartContract.Contract import Contract
from neo.Prompt.Commands import *
from neo.Prompt.Commands.Send import construct_and_send
from neo.Prompt.Utils import get_arg, get_from_addr, get_asset_id, lookup_addr_str, get_tx_attr_from_args, get_owners_from_params
from neocore.Fixed8 import Fixed8
from neocore.KeyPair import KeyPair
from neo.Core.TX.Transaction import TransactionOutput, ContractTransaction
from neo.Core.Blockchain import Blockchain
from neo.Wallets.utils import to_aes_key
from neo.Wallets import Wallet
from neo.Network.NodeLeader import NodeLeader
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from neo.Settings import settings
from neo.api.REST.RestApi import RestApi


from neo.Implementations.Notifications.LevelDB.NotificationDB import NotificationDB


class MakeMultisig:
    go_on = True

    _walletdb_loop = None
    Wallet = None

    def openWallet(self):
        if self.Wallet:
            self.closeWallet()

        self.Wallet = UserWallet.Open(path, to_aes_key(password))
        self.start_wallet_loop()

    def closeWallet(self):
        if self.Wallet:
            self.stop_wallet_loop()
            self.Wallet.Close()
            self.Wallet = None

    def start_wallet_loop(self):
        self._walletdb_loop = task.LoopingCall(self.Wallet.ProcessBlocks)
        self._walletdb_loop.start(1)

    def stop_wallet_loop(self):
        self._walletdb_loop.stop()
        self._walletdb_loop = None

    def rebuildWallet(self, num=0):
        if self.Wallet:
            self.stop_wallet_loop
            self.Wallet.Rebuild()
            if num > 0:
                self.Wallet._current_height = num
            self.start_wallet_loop

    def makeMultisig(self, target_pubkey):
        wallets = []
        i = 0
        tx_json = None
        dbloops = []
        pubkey = self.Wallet.PubKeys()[0]['Public Key']
        multisig_args = [pubkey, 1, target_pubkey, pubkey]

        pubkey = multisig_args[0]
        m = multisig_args[1]
        publicKeys = multisig_args[2:]

        pubkey_script_hash = Crypto.ToScriptHash(pubkey, unhex=True)
        verification_contract = Contract.CreateMultiSigContract(pubkey_script_hash, int(m), publicKeys)
        address = verification_contract.Address
        self.Wallet.AddContract(verification_contract)

        print("Added multi-sig contract address %s to wallet" % address)
        return address

    def removekey(self, d, key):
        r = dict(d)
        del r[key]
        return r

    def run(self):
        # settings.set_loglevel(logging.DEBUG)
        # settings.set_log_smart_contract_events(True)

        self.closeWallet()
        self.openWallet()
        self.rebuildWallet(1564945)
        # self.rebuildWallet(1620000)
        print(self.Wallet.ToJson()['percent_synced'])
        while self.Wallet._current_height < Blockchain.Default().Height:
            print("Wallet %s / Blockchain %s" % (str(self.Wallet._current_height), str(Blockchain.Default().Height)))
            sleep(10)
        currentkeys = targetkeys
        currentblock = Blockchain.Default().Height
        while currentkeys != {}:
            for targetkey in currentkeys:
                self.closeWallet()
                self.openWallet()
                multisig_addr = self.makeMultisig(targetkey)
                try:
                    gas_amount = currentkeys[targetkey]['gas']
                except:
                    gas_amount = 0
                    pass
                try:
                    neo_amount = currentkeys[targetkey]['neo']
                except:
                    neo_amount = 0
                    pass
                if gas_amount > 5000:
                    gas_amount = 5000
                if neo_amount > 5000:
                    neo_amount = 5000
                if neo_amount is None:
                    neo_amount = 0
                if gas_amount is None:
                    gas_amount = 0
                argsGAS = ['GAS', multisig_addr, str(gas_amount)]
                argsNEO = ['NEO', multisig_addr, str(neo_amount)]
                # argsGAS = ['GAS', multisig_addr, str(1)]  # testing
                # argsNEO = ['NEO', multisig_addr, str(1)]  # testing

                while self.Wallet._current_height < Blockchain.Default().Height:
                    print("Wallet %s / Blockchain %s" % (str(self.Wallet._current_height), str(Blockchain.Default().Height)))
                    sleep(5)
                if neo_amount == 0:
                    neo_is_sent = true
                else:
                    neo_is_sent = construct_and_send(to_aes_key(password),
                                                     self.Wallet, argsNEO,
                                                     prompt_password=False)
                if gas_amount == 0:
                    gas_is_sent = true
                else:
                    gas_is_sent = construct_and_send(to_aes_key(password),
                                                     self.Wallet, argsGAS,
                                                     prompt_password=False)

                if neo_is_sent:
                    currentkeys[targetkey] = self.removekey(
                                            currentkeys[targetkey], "neo")
                if gas_is_sent:
                    currentkeys[targetkey] = self.removekey(
                                            currentkeys[targetkey], "gas")

                if neo_is_sent and gas_is_sent:
                    currentkeys = self.removekey(currentkeys, targetkey)
                # for key in currentkeys:
                #     print(key)
                print("sleep 100")
                sleep(100)
                while currentblock == Blockchain.Default().Height:
                    print("waiting for block to sync")
                    print("Wallet %s / Blockchain %s" % (str(self.Wallet._current_height), str(Blockchain.Default().Height)))
                    sleep(10)
                currentblock = Blockchain.Default().Height
        print("sent")
        f.close()

def main():
    # Use Private Testnet
    settings.setup('protocol.stevenet.json')

    # Instantiate the blockchain and subscribe to notifications
    blockchain = LevelDBBlockchain(settings.chain_leveldb_path)
    Blockchain.RegisterBlockchain(blockchain)

    # Try to set up a notification db
    if NotificationDB.instance():
        NotificationDB.instance().start()

    dbloop = task.LoopingCall(Blockchain.Default().PersistBlocks)
    dbloop.start(.1)


    # Start the prompt interface
    cli = MakeMultisig()

    # Run things
    reactor.suggestThreadPoolSize(15)
    reactor.callInThread(cli.run)
    NodeLeader.Instance().Start()

    # Starts a thread with custom LANGUAGE_CODE
    d = threading.Thread(target=custom_background_code)
    d.setDaemon(True)
    d.start()

    # REST api
    logger.info("Starting REST api server at %s" % ("placeholder"))
    api_server_rest = RestApi()



    # reactor.run() is blocking, until `quit()` is called which stops the reactor
    reactor.run()

    # After the reactor is stopped, gracefully shutdown the database.
    NotificationDB.close()
    Blockchain.Default().Dispose()
    NodeLeader.Instance().Shutdown()


if __name__ == "__main__":
    main()
