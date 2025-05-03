from Grabber import user_collection

async def smex(id):
    all_users = user_collection.find()
    all_users = await all_users.to_list(length=None)
    user_balances = {user['id']: int(user.get('balance', 0)) for user in all_users}


    sorted_balances = sorted(user_balances.items(), key=lambda item: item[1], reverse=True)


    for rank, (user_id, balance) in enumerate(sorted_balances, start=1):
        if user_id == id:
            return rank
    return None  

async def show(user_id):
    user = await user_collection.find_one({"id": user_id})
    if user:
        return int(user.get("balance", 0))
    return 0

async def add(user_id, balance):
    x = await user_collection.find_one({'id': user_id})
    if not x:
        return
    x['balance'] = str(int(x.get('balance', 0)) + balance)
    x.pop('_id')
    await user_collection.update_one({'id': user_id}, {'$set': x}, upsert=True)

async def deduct(user_id, balance):
    x = await user_collection.find_one({'id': user_id})
    if not x:
        return
    x['balance'] = str(int(x.get('balance')) - balance)
    x.pop('_id')
    await user_collection.update_one({'id': user_id}, {'$set': x}, upsert=True)

async def abank(user_id, balance):
    x = await user_collection.find_one({'id': user_id})
    if not x:
        return
    x['saved_amount'] = str(int(x.get('saved_amount', 0)) + balance)
    x.pop('_id')
    await user_collection.update_one({'id': user_id}, {'$set': x}, upsert=True)

async def dbank(user_id, balance):
    x = await user_collection.find_one({'id': user_id})
    if not x:
        return
    x['saved_amount'] = str(int(x.get('saved_amount', 0)) - balance)
    x.pop('_id')
    await user_collection.update_one({'id': user_id}, {'$set': x}, upsert=True)

async def sbank(user_id):
    x = await user_collection.find_one({"id": user_id})
    if x:
        return int(x.get("saved_amount", 0))
    return 0

async def aruby(user_id, balance):
    x = await user_collection.find_one({'id': user_id})
    if not x:
        return
    x['rubies'] = str(int(x.get('rubies', 0)) + balance)
    x.pop('_id')
    await user_collection.update_one({'id': user_id}, {'$set': x}, upsert=True)

async def druby(user_id, balance):
    x = await user_collection.find_one({'id': user_id})
    if not x:
        return
    x['rubies'] = str(int(x.get('rubies', 0)) - balance)
    x.pop('_id')
    await user_collection.update_one({'id': user_id}, {'$set': x}, upsert=True)

async def sruby(user_id):
    x = await user_collection.find_one({"id": user_id})
    if x:
        return int(x.get("rubies", 0))
    return 0

async def agold(user_id, balance):
    x = await user_collection.find_one({'id': user_id})
    if not x:
        return
    x['gold'] = str(int(x.get('gold', 0)) + balance)
    x.pop('_id')
    await user_collection.update_one({'id': user_id}, {'$set': x}, upsert=True)

async def dgold(user_id, balance):
    x = await user_collection.find_one({'id': user_id})
    if not x:
        return
    x['gold'] = str(int(x.get('gold', 0)) - balance)
    x.pop('_id')
    await user_collection.update_one({'id': user_id}, {'$set': x}, upsert=True)

async def sgold(user_id):
    x = await user_collection.find_one({"id": user_id})
    if x:
        return int(x.get("gold", 0))
    return 0