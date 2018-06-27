import threading
import getpass
import logging
from time import sleep
from logzero import logger
from constants import path, password, from_address

from twisted.internet import reactor, task
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

from neo.Implementations.Notifications.LevelDB.NotificationDB import NotificationDB

# targetkey = '033ec803d110ad793aab8171847afbceef842f54ac0290bd4af074590ade29c08e'

targetkeys = {
    '0304a7c9298b923e2178f5c1bbe7d5afb8faca56766f25288f90a7659e63c78d19': {
        'neo': 100,
        'gas': 500,
        'email': 'karthik'
    },
    '02a88fd1ce1f06977a5081c5f41ef8a46ad5227788fda0de93eb1340b6eb8eb1d1': {
        'neo': 10000,
        'gas': 10000,
        'email': 'Nikolay'
    },
    '02c717c116067b4e88fa1300b0f2922df2bc28cf3303e5572b3c6532383dfaa7fc': {
        'neo': 5000,
        'gas': 5000,
        'email': 'arrix'
    },
    '03221ed42361d4490328840637a6a9b7f4ea94fc3cabfe1b8959c59a7d6acc70ab': {
        'neo': 500,
        'gas': 10000,
        'email': 'Sabarish'
    },
}



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
        dbloop = task.LoopingCall(Blockchain.Default().PersistBlocks)
        dbloop.start(.1)
        self.closeWallet()
        self.openWallet()
        print(self.Wallet.ToJson()['percent_synced'])
        while self.Wallet._current_height < Blockchain.Default().Height:
            print("Wallet %s / Blockchain %s" % (str(self.Wallet._current_height), str(Blockchain.Default().Height)))
            sleep(1)
        f = open("request_neo2002.csv", "w")
        f.write('targetkey')
        f.write(',')
        f.write('neo')
        f.write(',')
        f.write('neo sent')
        f.write(',')
        f.write('gas')
        f.write(',')
        f.write('gas sent')
        f.write(',')
        f.write('multisig')
        f.write(',')
        f.write('email')
        f.write('\n')
        currentkeys = targetkeys
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
                if gas_amount > 1000:
                    gas_amount = 1000
                if neo_amount > 1000:
                    neo_amount = 1000

                argsGAS = ['GAS',multisig_addr,str(gas_amount)]#testing
                argsNEO = ['NEO',multisig_addr,str(neo_amount)]#testing
                # argsGAS = ['GAS',multisig_addr,str(1)]#testing
                # argsNEO = ['NEO',multisig_addr,str(1)]#testing

                while self.Wallet._current_height < Blockchain.Default().Height:
                    print("Wallet %s / Blockchain %s" % (str(self.Wallet._current_height), str(Blockchain.Default().Height)))
                    sleep(5)
                neo_is_sent = construct_and_send(to_aes_key(password), self.Wallet, argsNEO, prompt_password=False)
                gas_is_sent = construct_and_send(to_aes_key(password), self.Wallet, argsGAS, prompt_password=False)
                if neo_is_sent and gas_is_sent:
                    f.write(targetkey)
                    f.write(',')
                    f.write(str(neo_amount))
                    f.write(',')
                    if neo_is_sent:
                        f.write("yes")
                    else:
                        f.write("no")
                    f.write(',')
                    f.write(str(gas_amount))
                    f.write(',')
                    if gas_is_sent:
                        f.write("yes")
                    else:
                        f.write("no")
                    f.write(',')
                    f.write(multisig_addr)
                    f.write(',')
                    f.write(targetkeys[targetkey]['email'])
                    f.write('\n')
                    currentkeys = self.removekey(currentkeys, targetkey)
                else:
                    if neo_is_sent:
                        currentkeys[targetkey] = self.removekey(currentkeys[targetkey], "neo")
                    elif gas_is_sent:
                        currentkeys[targetkey] = self.removekey(currentkeys[targetkey], "gas")
        print("sent")
        f.close()
        # argsGAS = ['GAS','AK5q8peiC4QKwuZHWX5Dkqhmar1TAGvZBS',str(1)]#testing
        # argsNEO = ['NEO','AK5q8peiC4QKwuZHWX5Dkqhmar1TAGvZBS',str(1)]#testing
        # print("Wallet %s / Blockchain %s" % (str(self.Wallet._current_height), str(Blockchain.Default().Height)))
        #
        # while self.Wallet._current_height < Blockchain.Default().Height:
        #     print("Wallet %s / Blockchain %s" % (str(self.Wallet._current_height), str(Blockchain.Default().Height)))
        #     sleep(15)
        # construct_and_send(to_aes_key(password), self.Wallet, argsNEO, prompt_password=False)
        # construct_and_send(to_aes_key(password), self.Wallet, argsGAS, prompt_password=False)
        # print("sent")

def main():
    # Use TestNet
    settings.setup_testnet()

    # Instantiate the blockchain and subscribe to notifications
    blockchain = LevelDBBlockchain(settings.chain_leveldb_path)
    Blockchain.RegisterBlockchain(blockchain)

    # Try to set up a notification db
    if NotificationDB.instance():
        NotificationDB.instance().start()

    # Start the prompt interface
    cli = MakeMultisig()

    # Run things
#    reactor.suggestThreadPoolSize(15)
    reactor.callInThread(cli.run)
    NodeLeader.Instance().Start()

    # reactor.run() is blocking, until `quit()` is called which stops the reactor.
    reactor.run()

    # After the reactor is stopped, gracefully shutdown the database.
    NotificationDB.close()
    Blockchain.Default().Dispose()
    NodeLeader.Instance().Shutdown()


if __name__ == "__main__":
    main()
