import logging

from django.db.models import Max

from rdmo.projects.models import Value, Snapshot
from rdmo.domain.models import Attribute
from rdmo.questions.models import QuestionSet, Question 


log = logging.getLogger(__name__)


def makeSnapshot(project):
    snapshot = Snapshot()
    snapshot.project = project
    snapshot.title = 'automatically generated snapshot'
    snapshot.description = 'This snapshot was generated automatically before the data import from an external system.'
    snapshot.save()

def __importValue(project, valueText, attribute, setIndex=None, collectionIndex=None):
    isCollection = 0
    questionExists = 1

    try:
        question = Question.objects.get(attribute=attribute, questionset__section__catalog=project.catalog)
    except Question.DoesNotExist:
        log.info('Question not in db. Skipping.')
        questionExists = 0
        #print('Frage nicht in db')
    #    return
    
    if not questionExists:
        if attribute.key == 'id':
            try:
                questionSets = QuestionSet.objects.filter(attribute=attribute.parent, section__catalog=project.catalog, is_collection=1)
            except QuestionSet.DoesNotExist:
                log.info('QuestionSet not in db. Skipping.')
                #print('Fragenabschnitt nicht in db')
            if questionSets:
                isCollection = 1
    else:
        if question.is_collection or question.questionset.is_collection:
            isCollection = 1


    if not setIndex:
        setIndex = 0
    if not collectionIndex:
        collectionIndex = 0

    #print('###################################################################')
    #print('#Import value: '+str(valueText))
    #print('# - setIndex: ' + str(setIndex))
    #print('# - colIndex: ' + str(collectionIndex))
    #print('# - Import attribute: '+str(attribute))
    createNewValue = 1
    if isCollection == 0:
        try:
            #value = Value.objects.get(project=project, attribute=attribute, set_index=setIndex, collection_index=collectionIndex, snapshot=None)
            value = Value.objects.get(project=project, attribute=attribute, snapshot=None)
            createNewValue = 0
            #print('# - Value found')
            #print('#   - setIndex:' + str(value.set_index))
            #print('#   - colIndex:' + str(value.collection_index))
            #print('#   - Text:' + str(value.text))
            #print('#   - Attribute:' + str(value.attribute))
        except Value.DoesNotExist:
            log.info('Value not in db. Creating new value.')
            #print('#   - creating new value')

    if createNewValue:
        value = Value()
        value.project = project
        value.attribute = attribute
        value.set_index = setIndex
        value.collection_index = collectionIndex
        value.text = valueText
        value.value_type = 'Text'
    else:
        if value.text:
            value.text = value.text + '; ' + str(valueText)
        else:
            value.text = value.text + str(valueText)

    value.save()
    #print('###################################################################')

def importData(project, projectData, key=None, setIndex=None, collectionIndex=None):
    # if projectData is a list
    #print('ProjectData: '+str(projectData))
    if isinstance(projectData, list):
        #print('Attribut ist Liste ('+key+')')
        if key:
            try:
                domainAttribute = Attribute.objects.get(uri=key)
            except Attribute.DoesNotExist:
                log.info('Attribute %s not in db. Skipping.', key)
                return

            colIndexDict = Value.objects.filter(attribute=domainAttribute, project=project).aggregate(index=Max('collection_index'))
            colIndex = colIndexDict['index']
            if colIndex is None:
                colIndex = 0
            else:
                colIndex = colIndex + 1
            #print('max cindex: '+str(colIndex)+' ('+domainAttribute.uri+')')

            # call importData vor every element in list
            for attribute in projectData:
                #print('for attribute in projectData:')
                # if attribute is dictionary then:
                if isinstance(attribute, dict):
                    # get child attribute
                    childKey = next(iter(attribute))
                    try:
                        childAttribute = Attribute.objects.get(uri=childKey)
                    except Attribute.DoesNotExist:
                        log.info('Attribute %s not in db. Skipping.', childKey)
                        return

                    # get max setIndex of childs
                    sIndexDict = Value.objects.filter(attribute__parent=domainAttribute, project=project).aggregate(index=Max('set_index'))
                    sIndex = sIndexDict['index']
                    #print('max sindex: '+str(sIndex)+' ('+domainAttribute.uri+')')
                    if sIndex is None:
                        sIndex = 0
                    else:
                        sIndex = sIndex+1

                    for uri in attribute:
                        #print('subattribut ist dict ('+uri+')')
                        importData(project, attribute[uri], uri, sIndex, None)
                # else
                else:
                    if attribute:
                        #print('Attribut wird importiert ('+str(attribute)+')')
                        __importValue(project, attribute, domainAttribute, None, colIndex)
                colIndex = colIndex + 1
    # else if projectData is a dictionary:
    elif isinstance(projectData, dict):
        #print('Attribut ist dict')
        sIndex = 0
        for uri in projectData:
            # get child attribute
            try:
                childAttribute = Attribute.objects.get(uri=uri)
            except Attribute.DoesNotExist:
                log.info('Attribute %s not in db. Skipping.', uri)
                return

            # get max setIndex of childs
            sIndexDict = Value.objects.filter(attribute=childAttribute, project=project).aggregate(index=Max('set_index'))
            tmpSIndex = sIndexDict['index']
            if tmpSIndex is None:
                tmpSIndex = 0
            else:
                tmpSIndex = tmpSIndex + 1
            if tmpSIndex > sIndex:
                sIndex = tmpSIndex
        #print('max index: '+str(sIndex))

        for uri in projectData:
            importData(project, projectData[uri], uri, sIndex, None)
    # else projectData is a single Value
    else:
        if key:
            #print('Attribut ist value ('+key+')')
            try:
                domainAttribute = Attribute.objects.get(uri=key)
            except Attribute.DoesNotExist:
                log.info('Attribute %s not in db. Skipping.', key)
                #print('Attribut nicht in db')
                return
            if projectData:
                #print('Attribut wird importiert')
                __importValue(project, projectData, domainAttribute, setIndex, collectionIndex)


