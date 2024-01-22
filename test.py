import pymongo
 
myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["runoobdb"]
mycol = mydb["sites"]
 
mydict = { "name": "RUNOOB", "alexa": "10000" }
print("mydict: ")
x = mycol.insert_one(mydict) 
print(x)