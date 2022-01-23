from stellar_sdk import (
    Asset,
    Claimant,
    ClaimPredicate,
    Keypair,
    Network,
    Server,
    TransactionBuilder,
)
import json

x = json.load(open('make_claimable_info.json'))



# Put the private key here

pk = x["claimable_maker_pk"]

# Put the Asset information here

asset_code = "AQUA"
asset_issuer = "GBNZILSTVQZ4R7IKQDGHYGY2QXL5QOFJYQMXPKWRRM5PAV7Y4M67AQUA"
asset_amount = "0.001"

# Put transaction information here

tx_memo = ""


print()
print('==================== Started TransactionBuilder ====================')
print()
address_file = open('addresses.txt', 'r')

keypair = Keypair.from_secret(pk)
server = Server("https://horizon.stellar.org")
account = server.load_account(keypair.public_key)

tx = TransactionBuilder(source_account = account, network_passphrase = Network.PUBLIC_NETWORK_PASSPHRASE, base_fee = 1000)
op_count = 0
claimant_me = Claimant(destination=keypair.public_key)
batch = 0
for line in address_file:
    line = line.split()[0]
    claimant_you = Claimant(destination=line)
    if batch == 99:
        batch = 0
        tx.append_create_claimable_balance_op(
        asset=Asset(asset_code,asset_issuer),
        amount=asset_amount,
        claimants=[claimant_you,claimant_me],
        source=keypair.public_key
        )
        tx.add_text_memo(tx_memo)
        completed = tx.build()
        completed.sign(keypair)
        sub = server.submit_transaction(completed)
        tx = TransactionBuilder(source_account = account, network_passphrase = Network.PUBLIC_NETWORK_PASSPHRASE, base_fee = 1000)
    else:
        tx.append_create_claimable_balance_op(
        asset=Asset(asset_code,asset_issuer),
        amount=asset_amount,
        claimants=[claimant_you,claimant_me],
        source=keypair.public_key
        )
        batch +=1
        op_count += 1
        print(f'op: {op_count}, made {asset_code} claimable for {line}')
completed = tx.build()
completed.sign(keypair)
sub = server.submit_transaction(completed)
print(sub)
print()
print()
print('==================== Success ====================')
print()


