import interpreter
import bufferManager, catalogManager, recordManager, indexManager

def execute(command):
    queryData=interpreter.interpret(command)
    # print(queryData)  # for DEBUG
    if queryData['operation']=='unknown':
        return {
            'status': 'error',
            'payload': 'Unknown SQL statement'
        }

    if queryData['data'] is not None and 'error' in queryData['data']:
        return {
            'status': 'error',
            'payload': queryData['data']['error']
        }


    if queryData['operation']=='insert':
        result=executeInsert(queryData['data'])
        if result['status'] == 'success':
            return {
                'status': 'success',
                'payload': 'Successfully inserted a record into table '+queryData['data']['tableName']
            }
        else:
            return result

    if queryData['operation']=='createTable':
        result=executeCreateTable(queryData['data'])
        if result['status']=='success':
            return {
                'status': 'success',
                'payload': 'Table '+queryData['data']['tableName']+' was successfully created.'
            }
        else:
            return result

    if queryData['operation']=='select':
        result=executeSelect(queryData['data'])
        if result['status'] == 'success':
            return {
                'status': 'success',
                'payload': result['payload']
            }
        else:
            return result

    if queryData['operation']=='delete':
        result=executeDelete(queryData['data'])
        if result['status']=='success':
            return {
                'status':'success',
                'payload': 'Successfully deleted '+str(result['payload'])+' records.'
            }
        return

    if queryData['operation']=='createIndex':
        result=executeCreateIndex(queryData['data'])
        if result['status'] == 'success':
            return {
                'status': 'success',
                'payload': 'Index '+queryData['data']['indexName']+' was successfully created.'
            }
        else:
            return result

    if queryData['operation']=='dropIndex':
        result=executeDropIndex(queryData['data'])
        if result['status'] == 'success':
            return {
                'status': 'success',
                'payload': 'Index ' + queryData['data']['indexName'] + ' was successfully removed.'
            }
        else:
            return result

    if queryData['operation']=='dropTable':
        result=executeDropTable(queryData['data'])
        if result['status'] == 'success':
            return {
                'status': 'success',
                'payload': 'Table ' + queryData['data']['tableName'] + ' was successfully removed.'
            }
        else:
            return result

    if queryData['operation']=='showTables':
        return executeShowTables()

    return {
        'status':'error',
        'payload':'Interpreter failed'
    }



def executeCreateTable(data):
    if catalogManager.existTable(data['tableName']):
        return {'status': 'error', 'payload': 'Table '+data['tableName']+' already exists'}
    fields = data['fields']
    for field in fields:
        if field['name']==data['primaryKey']:  # auto set primary key to unique
            field['unique']=True
    result=recordManager.createTable(data['tableName'])
    if result['status']=='error':
        return result
    result=catalogManager.createTable(data['tableName'], data['primaryKey'], fields)
    if result['status']=='error':
        return result
            # catalogManager.createIndex('auto$' + data['tableName'] + '$' + field['name'], data['tableName'],columnCount)
    columnCount=0
    for field in fields:
        if field['unique']:
            result=catalogManager.createIndex('auto$'+data['tableName']+'$'+field['name'],data['tableName'],columnCount)
            if result['status'] == 'error':
                return result
        columnCount+=1
    columnCount=0
    for field in fields:
        if field['unique']:
            result=indexManager.createIndex('auto$'+data['tableName']+'$'+field['name'],data['tableName'],columnCount)
            if result['status'] == 'error':
                return result
        columnCount+=1
    return {
        'status':'success',
        'payload':None
    }



def executeInsert(data):
    if not catalogManager.existTable(data['tableName']):
        return {'status': 'error', 'payload': 'Table does not exist'}
    return recordManager.insert(data['tableName'],data['values'])



def executeSelect(data):
    if not catalogManager.existTable(data['from']):
        return {'status': 'error', 'payload': 'Table '+data['from']+' does not exist'}
    fieldList=catalogManager.getFieldsList(data['from'])
    fields=[]
    for f in fieldList:
        fields.append(f['name'])
    head=[]
    if '*' in data['fields']:
        head=fields
    else:
        for field in data['fields']:
            if field in fields:
                head.append(field)
            else:
                return {'status': 'error', 'payload': 'Field ' + field + ' does not exist'}
    if data['orderBy'] is not None:
        orderByFieldNo=catalogManager.getFieldNumber(data['from'],data['orderBy'])
        if orderByFieldNo == -1:
            return {'status': 'error', 'payload': 'Field ' + data['fieldName'] + ' does not exist'}
    else:
        orderByFieldNo=None
    result=recordManager.select(data['from'],data['fields'],data['where'],orderByFieldNo,data['limit'])
    if result['status']=='error':
        return result
    return {
        'status':'success',
        'payload':{
            'head': head,
            'body': result['payload']
        }
    }



def executeCreateIndex(data):
    if catalogManager.existIndex(data['indexName']):
        return {'status': 'error', 'payload': 'Index already exists'}
    no=catalogManager.getFieldNumber(data['tableName'],data['fieldName'])
    if no==-1:
        return {'status': 'error', 'payload': 'Field '+data['fieldName']+' does not exist'}
    result=catalogManager.createIndex(data['indexName'],data['tableName'],no)
    if result['status']=='error':
        return result
    return indexManager.createIndex(data['indexName'],data['tableName'],no)



def executeDropIndex(data):
    if not catalogManager.existIndex(data['indexName']):
        return {'status': 'error', 'payload': 'Index does not exist'}
    result=indexManager.dropIndex(data['indexName'])
    if result['status']=='error':
        return result
    return catalogManager.dropIndex(data['indexName'])



def executeDropTable(data):
    if not catalogManager.existTable(data['tableName']):
        return {'status': 'error', 'payload': 'Table '+data['tableName']+' does not exist'}
    indices=catalogManager.getIndexList(data['tableName'])
    for index in indices:
        result=indexManager.dropIndex(index[0])
        if result['status'] == 'error':
            return result
        result=catalogManager.dropIndex(index[0])
        if result['status'] == 'error':
            return result
    result=recordManager.dropTable(data['tableName'])
    if result['status']=='error':
        return result
    return catalogManager.dropTable(data['tableName'])



def executeDelete(data):
    if not catalogManager.existTable(data['from']):
        return {'status': 'error', 'payload': 'Table '+data['tableName']+' does not exist'}
    return recordManager.delete(data['from'],data['where'])



def executeShowTables():
    tables=catalogManager.getTableNames()
    body=[]
    for table in tables:
        body.append([table])
    return {
        'status': 'success',
        'payload': {
            'head':['Table Name'],
            'body':body
        }
    }


def quit():
    indexManager.closeIndices()
    catalogManager.closeCatalog()
    bufferManager.saveAll()
    bufferManager.closeAllFiles()
