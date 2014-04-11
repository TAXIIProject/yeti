# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# For license information, see the LICENSE.txt file

"""
The entry point (of sorts) into this code is the 
evalate_critera() function, which calls all other 
functions

"""
ns_map = {'AddressObject': 'http://cybox.mitre.org/objects#AddressObject-2',
          'cyboxCommon': 'http://cybox.mitre.org/common-2'}

class QueryHelperException(Exception):
    def __init__(self, message, status_type, status_detail=None):
        Exception.__init__(self, message)
        self.status_type = status_type
        self.status_detail = status_detail or {}

def evaluate_criteria(criteria, stix_etree):
    """Evaluates a Criteria which contains at least one Criteria/Criterion child
    """
    operator = criteria.operator
    if operator not in ['OR','AND']:
        raise QueryHelperException('Operator was not OR or AND', 'BAD_MESSAGE')
    
    if len(criteria.criteria) + len(criteria.criterion) == 0:#No criteria/criterion to evaluate!
        raise QueryHelperException('No child Criteria or Criterion.', 'BAD_MESSAGE')
    
    for child in criteria.criteria:#Iterate over child criteria, evaluating each one
        value = evaluate_criteria(child, stix_etree)#Recursion
        if value and operator == 'OR':
            #If the operator is OR, any True result means this document matches the query
            return True
        elif not value and operator == 'AND':
            #If the operator is AND, any False result means this document doesn't match the query
            return False
        else:#Nothing can be determined for sure at this point
            #More processing is required to determine whether this document matches the query
            continue
    
    for child in criteria.criterion:#Iterate over child criterion, evaluating each one
        value = evaluate_criterion(child, stix_etree)
        if value and operator == 'OR':
            #If the operator is OR, any True result means this document matches the query
            return True
        elif not value and operator == 'AND':
            #If the operator is AND, any False result means this document doesn't match the query
            return False
        else:
            #More processing is required to determine whether this document matches the query
            continue#Nothing can be determined for sure at this point
    
    #If the operator is AND, then we have reached here because we haven't found any FALSE results
    #If the operator is OR, then we have reached here because we haven't found any TRUE results
    return operator == 'AND'#Returns True if the operator is AND, False if it is OR.

def evaluate_criterion(criterion, stix_etree):
    """Evaluates a Criterion"""
    if criterion.test.capability_id != 'urn:taxii.mitre.org:query:capability:core-1':#This code only supports the CORE capability module
        raise QueryHelperException('Unsupported Capability Module', 'UNSUPPORTED_CAPABILITY_MODULE', {'CAPABILITY_MODULE': 'urn:taxii.mitre.org:query:capability:core-1'})
    
    target_xpath, operand = target_to_xpath(criterion.target)
    
    xpath_string = build_full_xpath(target_xpath, operand, criterion.test.relationship, criterion.test.parameters)
    matches = stix_etree.xpath(xpath_string, namespaces=ns_map)
    if matches in (True, False):
        result = matches
    else:
        result = len(matches) > 0
    
    if criterion.negate:
        return not result
    return result

def target_to_xpath(target):
    """
    Takes a target string and turns it into an XPath for use in 
    this implementation's query. A "real" implementation would
    probably have a much more robust method here.
    
    This function currently implements a direct mapping of target to XPath.
    It is possible to make something much more robust, if desired.
    """
    operand = 'text()'
    ret_target = None
    if target == '//Address_Value':
        ret_target = '//AddressObject:Address_Value'
    elif target == '//Hash/Simple_Hash_Value':
        ret_target = '//cyboxCommon:Hash/cyboxCommon:Simple_Hash_Value'
    else:
        raise QueryHelperException('Targeting Expression Not Supported!', 
                                   'UNSUPPORTED_TARGETING_EXPRESSION', 
                                   {'PREFERRED_SCOPE': '//Hash/Simple_Hash_Value', 'ALLOWED_SCOPE': '//Address_Value'})
    
    return ret_target, operand

def build_full_xpath(xpath_string, operand, relationship, params):
    """
        Takes an XPath, an operand, a relationship and the params (as a dict) and 
        builds the full XPath to be evaluated. This function results in things like:
        '/some/xpath[text() == the_supplied_value]'
    """
    if relationship not in ['equals','not equals',
                            'greater than','greater than or equal',
                            'less than','less than or equal',
                            'does not exist','exists',
                            'begins with','ends with','contains']:
        raise QueryHelperException('Relationship not in CORE capability module!', 'BAD_MESSAGE')
    
    if 'value' in params:
        v = params['value']
    else:
        v = None
    append = ''
    if relationship == 'equals':
        if params['match_type'] == 'case_sensitive_string':
            append = '[%s = \'%s\']' % (operand, v)
        elif params['match_type'] == 'case_insensitive_string':
            append = '[translate(%s, \'ABCDEFGHIJKLMNOPQRSTUVWXYZ\', \'abcdefghijklmnopqrstuvwxyz\') = \'%s\']' % (operand, v.lower())
        elif params['match_type'] == 'number':
            append = '[%s = \'%s\']' % (operand, v)
    elif relationship == 'not equals':
        if params['match_type'] == 'case_sensitive_string':
            append = '[%s != \'%s\']' % (operand, v)
        elif params['match_type'] == 'case_insensitive_string':
            append = '[translate(%s, \'ABCDEFGHIJKLMNOPQRSTUVWXYZ\', \'abcdefghijklmnopqrstuvwxyz\') != \'%s\']' % (operand, v.lower())
        elif params['match_type'] == 'number':
            append = '[%s != \'%s\']' % (operand, v)
    elif relationship == 'greater than':
        append = '[%s > \'%s\']' % (operand, v)
    elif relationship == 'greater than or equal':
        append = '[%s >= \'%s\']' % (operand, v)
    elif relationship == 'less than':
        append = '[%s < \'%s\']' % (operand, v)
    elif relationship == 'less than or equal':
        append = '[%s <= \'%s\']' % (operand, v)
    elif relationship == 'does not exist':
        xpath_string = 'not(' + xpath_string + ')'
    elif relationship == 'exists':
        pass#nothing necessary
    elif relationship == 'begins with':
        if params['case_sensitive'] == 'false':
            append = '[starts-with(translate(%s, \'ABCDEFGHIJKLMNOPQRSTUVWXYZ\', \'abcdefghijklmnopqrstuvwxyz\'), \'%s\')]' % (operand, v.lower())
        elif params['case_sensitive'] == 'true':
            append = '[starts-with(%s, \'%s\')]' % (operand, v)
    elif relationship == 'ends with':
        if params['case_sensitive'] == 'false':
            append = '[substring(translate(%s, \'ABCDEFGHIJKLMNOPQRSTUVWXYZ\', \'abcdefghijklmnopqrstuvwxyz\'), string-length(%s) - string-length(\'%s\') + 1) = \'%s\']' % (operand, operand, v, v.lower())
        elif params['case_sensitive'] == 'true':
            append = '[substring(%s, string-length(%s) - string-length(\'%s\') + 1) = \'%s\']' % (operand, operand, v, v)
    elif relationship == 'contains':
        if params['case_sensitive'] == 'false':
            append = '[contains(translate(%s, \'ABCDEFGHIJKLMNOPQRSTUVWXYZ\', \'abcdefghijklmnopqrstuvwxyz\'), \'%s\')]' % (operand, v.lower())
        elif params['case_sensitive'] == 'true':
            append = '[contains(%s, \'%s\')]' % (operand, v)
    else:
        raise QueryHelperException('Relationship not in CORE capability module!', 'BAD_MESSAGE')
    
    xpath_string += append
    return xpath_string

