import threading
import getpass
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

targetkey = '033ec803d110ad793aab8171847afbceef842f54ac0290bd4af074590ade29c08e'


def make_multisig(target_pubkey, wallet):
    wallets = []
    i = 0
    tx_json = None
    dbloops = []
    pubkey = wallet.PubKeys()[0]['Public Key']
    multisig_args = [pubkey, 1, target_pubkey, pubkey]

    pubkey = multisig_args[0]
    m = multisig_args[1]
    publicKeys = multisig_args[2:]

    pubkey_script_hash = Crypto.ToScriptHash(pubkey, unhex=True)
    verification_contract = Contract.CreateMultiSigContract(pubkey_script_hash, int(m), publicKeys)
    address = verification_contract.Address
    wallet.AddContract(verification_contract)

    print("Added multi-sig contract address %s to wallet" % address)
    return address


def custom_background_code():
    wallet = UserWallet.Open(path, to_aes_key(password))
    multisig_addr = make_multisig(targetkey, wallet)
    args = ['GAS','AK5q8peiC4QKwuZHWX5Dkqhmar1TAGvZBS','1']#testing

    construct_and_send('', wallet, args)


def start_neo():
    # Use TestNet
    settings.setup_testnet()

    # Setup the blockchain
    blockchain = LevelDBBlockchain(settings.chain_leveldb_path)
    Blockchain.RegisterBlockchain(blockchain)
    dbloop = task.LoopingCall(Blockchain.Default().PersistBlocks)
    dbloop.start(.1)
    NodeLeader.Instance().Start()

    # Start a thread with custom code
    d = threading.Thread(target=custom_background_code)
    d.setDaemon(True)  # daemonizing the thread will kill it when the main thread is quit
    d.start()

    # Run all the things (blocking call)
    reactor.run()
    logger.info("Shutting down.")

start_neo()
