from stellar_sdk import Asset,Claimant,ClaimPredicate,Keypair,Network,Server,TransactionBuilder
import requests
from datetime import datetime
import json
import time

pk = ""

keypair = Keypair.from_secret(pk)

def format_date(x):
    x = x.split('T')
    date = x[0].split('-')
    time = x[1].split('Z')[0]
    new_str = f"{date[2]}/{date[1]}/{date[0][2:5]} {time}"
    return new_str

def find_trustlines(address):
    # print("searching for trustlines...") 
    print()
    trustlines = []
    acc_url = f"https://horizon.stellar.org/accounts/{address}"
    x = requests.get(acc_url).json()['balances']
    t = list(filter(lambda x:x["asset_type"]=="credit_alphanum4",x))
    for i in t:
        trustlines.append(f"{i['asset_code']}:{i['asset_issuer']}")
        # print(f"found trustline: {i['asset_code']}")
    return trustlines

def is_claimable(predicate_tree,key):
    x = (list(filter(lambda x:x["destination"]==key,predicate_tree))[0])
    # print({"x" : x})
    p = x["predicate"]
    now = datetime.utcnow()
    if  p == {"unconditional" : True}:
        return True
    else:
        if 'abs_before' in p:
            # print('claim before: ' + format_date(p["abs_before"]))
            claim_before = format_date(p["abs_before"])
            before_date = datetime.strptime(claim_before, '%d/%m/%y %H:%M:%S') 
            if now < before_date:
                return True
            else:
                return False
        elif 'and' in p:
            claim_before = format_date(p["and"][0]["abs_before"])
            claim_after = format_date(p["and"][1]["not"]["abs_before"])
            before_date = datetime.strptime(claim_before, '%d/%m/%y %H:%M:%S') 
            after_date = datetime.strptime(claim_before, '%d/%m/%y %H:%M:%S')
            if now>after_date and now<before_date:
                return True
            else:
                return False
        else:
            return False

def linear_search(array, to_find):
	for i in range(0, len(array)):
		if array[i] == to_find:
			return True
	return False

def find_claims(address):
    # print("searching for claimable balances...")
    print()
    valid_claimables = []
    acc_url = f"https://horizon.stellar.org/claimable_balances?claimant={address}&limit=100"
    cbal = requests.get(acc_url).json()["_embedded"]["records"]
    for i in cbal:
        valid = is_claimable(i['claimants'],address)
        if valid:
            valid_claimables.append({"id" : i['id'], "trustline":i["asset"]})
            # print(f"balance: {i['id']} is claimable: {valid}")
        else:
            continue
    return valid_claimables

def needed_trust(bal,trust):
    needed_tr = []
    for i in bal:
        z = (linear_search(trust,i['trustline']))
        if not z:
            needed_tr.append(i['trustline'])
    return needed_tr
        
bals = find_claims(keypair.public_key)
trusts = find_trustlines(keypair.public_key)
new_trusts = needed_trust(bals,trusts)

def set_trustlines(needed_trust,keyp):
    server = Server("https://horizon.stellar.org")
    account = server.load_account(keyp.public_key)    
    tx = TransactionBuilder(source_account = account, network_passphrase = Network.PUBLIC_NETWORK_PASSPHRASE, base_fee = 1000)
    op = 0
    for i in needed_trust:
        i = i.split(':')
        aco = i[0]
        asi = i[1]
        # tx.append_change_trust_op(asset_code=aco, asset_issuer=asi)
        tx.append_change_trust_op(asset=Asset(aco,asi))

        op +=1
    print("setting trustlines")
    if op != 0:
        complete = tx.build()
        complete.sign(keyp)
        resp3 = server.submit_transaction(complete)
    else:
        print("no new trustlines added")
def batch_submit(keyp, claims, needed_trust):
    batch_count = 0
    server = Server("https://horizon.stellar.org")
    account = server.load_account(keyp.public_key)
    tx = TransactionBuilder(source_account = account, network_passphrase = Network.PUBLIC_NETWORK_PASSPHRASE, base_fee = 1000)

    # for i in claims:
    #     tx.append_claim_claimable_balance_op(balance_id = i['id'], source = keyp.public_key)
    #     batch_count += 1
    #     print(f"op count: {batch_count}; Claiming {i['id']}")
    if batch_count == 100:
        complete = tx.build()
        complete.sign(keyp)
        resp3 = server.submit_transaction(complete)
        print(resp3)
        print("=============================Success=================================")
    
    else:
        # if len(needed_trust) != 0:    
        #     for i in needed_trust:
        #         tx.append_change_trust_op(Asset(i["asset_ticker"],i["asset_issuer"]))
        #         batch_count +=1        
        # else:
        #     print("no new trustlines needed")
        if len(claims) != 0:
            print("Starting to claim balances...")
            for i in claims:
                tx.append_claim_claimable_balance_op(balance_id=i['id'],source=keyp.public_key)
                batch_count += 1
                print(f"operation {batch_count}, claiming {i['id']}")
        else:
            print("no valid claimable balances to claim")
            
    if batch_count == 0:
        print("claimed all balances")
    else:
        complete = tx.build()
        complete.sign(keyp)
        resp3 = server.submit_transaction(complete)
        print(resp3)
        print("=============================Success=================================")


while(True):
    bals = find_claims(keypair.public_key)
    trusts = find_trustlines(keypair.public_key)
    new_trusts = needed_trust(bals,trusts)
    set_trustlines(new_trusts,keypair)
    batch_submit(keypair, bals,new_trusts)