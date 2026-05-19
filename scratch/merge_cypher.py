
import re

def generate_query_for_rule(rule_id, body):
    target_node = "Node"
    if "ID Data" in body: target_node = "IDData"
    elif "Contract Data" in body or "Contract record" in body: target_node = "ContractTerms"
    elif "Transaction Data" in body: target_node = "TransactionData"
    elif "Filing" in body: target_node = "Filing"

    if "D.3.9." in rule_id:
        f_type = 'New'
        if 'D.3.9.2' in rule_id or 'D.3.9.7' in rule_id: f_type = 'Replace'
        elif 'D.3.9.3' in rule_id or 'D.3.9.8' in rule_id: f_type = 'Delete'
        return f"""MATCH (f:Filing)-[:HAS_ID_DATA]->(id:IDData)
WHERE id.filing_type = '{f_type}'
MATCH (f)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION*1..3]->(item)
WHERE item.FilingType <> 'New'
MERGE (v:Violation {{RuleID: '{rule_id}', CID: f.CID, FilingPeriod: f.FilingPeriod}})
ON CREATE SET v.Message = 'Filing header (IDData) is {f_type} but component ' + labels(item)[0] + ' is ' + item.FilingType, v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)"""

    if rule_id in ['F.16.18', 'F.16.19', 'F.16.20.1']:
        h_type = 'New' if '18' in rule_id else ('Replace' if '19' in rule_id else 'Delete')
        return f"""MATCH (f:Filing)-[:HAS_ID_DATA]->(id:IDData)
WHERE id.filing_type = '{h_type}'
MATCH (f)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION*1..3]->(item)
WHERE item.FilingType <> 'New'
MERGE (v:Violation {{RuleID: '{rule_id}', CID: f.CID, FilingPeriod: f.FilingPeriod}})
ON CREATE SET v.Message = 'Overall filing type {h_type} requires all elements to be New', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)"""

    if rule_id in ['F.16.13', 'F.16.11', 'F.16.21']:
        if rule_id == 'F.16.13':
            return """MATCH (f:Filing)-[:HAS_ID_DATA]->(id:IDData)
WHERE id.Field_1_FilerUniqueID IS NULL OR id.Field_2_CompanyName IS NULL OR id.Field_4_ContactName IS NULL OR id.Field_6_Email IS NULL
MERGE (v:Violation {RuleID: 'F.16.13', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'ID Data Incomplete (Fields 1-14)', v.Severity = 'Error'
MERGE (id)-[:HAS_VIOLATION]->(v)"""
        if rule_id == 'F.16.11':
            return """MATCH (f:Filing)-[:HAS_CONTRACT]->(c:Contract)-[:HAS_TERMS]->(ct:ContractTerms)
WHERE ct.Field_15_ContractUniqueID IS NULL OR ct.Field_16_SellerCompanyName IS NULL OR ct.Field_17_CustomerCompanyName IS NULL OR ct.Field_30_ProductName IS NULL
MERGE (v:Violation {RuleID: 'F.16.11', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Contract Data Incomplete (Fields 15-44)', v.Severity = 'Error'
MERGE (ct)-[:HAS_VIOLATION]->(v)"""
        if rule_id == 'F.16.21':
            return """MATCH (f:Filing)-[:HAS_CONTRACT]->(c)-[:HAS_TERMS]->(ct)-[:HAS_TRANSACTION]->(t:TransactionData)
WHERE t.Field_45_TransactionUniqueID IS NULL OR t.Field_63_ProductName IS NULL OR t.Field_64_Quantity IS NULL OR t.Field_65_Price IS NULL
MERGE (v:Violation {RuleID: 'F.16.21', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Transaction Data Incomplete (Fields 45-72)', v.Severity = 'Error'
MERGE (t)-[:HAS_VIOLATION]->(v)"""

    if rule_id in ['F.16.25', 'F.16.4.2']:
        field = "Field_45_TransactionUniqueID" if rule_id == 'F.16.25' else "Field_1_FilerUniqueID"
        label = "TransactionData" if rule_id == 'F.16.25' else "IDData"
        return f"""MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(node:{label})
WITH f, node.{field} AS uid, collect(node) AS nodes
WHERE size(nodes) > 1
UNWIND nodes AS n
MERGE (v:Violation {{RuleID: '{rule_id}', CID: f.CID, FilingPeriod: f.FilingPeriod}})
ON CREATE SET v.Message = 'Duplicate ID: ' + uid, v.Severity = 'Error'
MERGE (n)-[:HAS_VIOLATION]->(v)"""

    if rule_id == 'F.16.8':
        return """MATCH (f:Filing)-[:HAS_ID_DATA]->(id:IDData)-[:HAS_CONTACT]->(c:Contact)
WHERE NOT c.Field_6_Email =~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\\\.[A-Za-z]{2,}$'
MERGE (v:Violation {RuleID: 'F.16.8', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Invalid email format: ' + c.Field_6_Email, v.Severity = 'Error'
MERGE (c)-[:HAS_VIOLATION]->(v)"""

    if rule_id == 'F.25.18':
        return """MATCH (f:Filing)-[:HAS_CONTRACT]->(c)-[:HAS_TERMS]->(ct:ContractTerms)-[:HAS_TRANSACTION]->(t:TransactionData)
WHERE t.Field_63_ProductName <> ct.Field_30_ProductName
MERGE (v:Violation {RuleID: 'F.25.18', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Product Mismatch: Transaction (' + t.Field_63_ProductName + ') vs Contract (' + ct.Field_30_ProductName + ')', v.Severity = 'Error'
MERGE (t)-[:HAS_VIOLATION]->(v)"""

    if rule_id == 'F.24.3':
        return """MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION*1..3]->(t:TransactionData)
WHERE t.Field_52_TransactionEndDate <= t.Field_51_TransactionBeginDate
MERGE (v:Violation {RuleID: 'F.24.3', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Temporal Error: End Date is not after Begin Date', v.Severity = 'Error'
MERGE (t)-[:HAS_VIOLATION]->(v)"""

    field_match = re.search(r'Field (\d+)', body)
    if field_match:
        fnum = field_match.group(1)
        prop = f"Field_{fnum}"
        if "after Jan 1, 1900" in body or "before 1900" in body:
            return f"""MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:{target_node})
WHERE item.{prop} IS NOT NULL AND item.{prop} < '1900-01-01'
MERGE (v:Violation {{RuleID: '{rule_id}', CID: f.CID, FilingPeriod: f.FilingPeriod}})
ON CREATE SET v.Message = 'Date check failed for Field {fnum}', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)"""

    return f"""MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:{target_node})
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {{RuleID: '{rule_id}', CID: f.CID, FilingPeriod: f.FilingPeriod}})
ON CREATE SET v.Message = 'Rule {rule_id} validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)"""

def clean_and_regenerate():
    with open('/home/raynier/Development/workspaces/fullstack/vibes/TOWER_WORKSPACE/scratch/validation_rules.md', 'r') as f:
        content = f.read()

    header_pattern = r'(## Original Req\. ID: .*)'
    parts = re.split(header_pattern, content)
    
    intro = parts[0]
    rule_parts = parts[1:]
    
    new_content = [intro]
    for i in range(0, len(rule_parts), 2):
        id_line = rule_parts[i]
        body_with_junk = rule_parts[i+1]
        
        rule_id = id_line.replace('## Original Req. ID: ', '').strip()
        
        clean_body = []
        for line in body_with_junk.split('\n'):
            # Filter out any Cypher-like lines
            s = line.strip()
            if s.startswith('### cypher query') or s.startswith('```') or s.startswith('MATCH ') or s.startswith('WHERE ') or s.startswith('MERGE ') or s.startswith('ON CREATE ') or s.startswith('// '):
                continue
            clean_body.append(line)
            
        body_text = "\n".join(clean_body).strip()
        query = generate_query_for_rule(rule_id, body_text)
        
        new_content.append(f"{id_line}\n{body_text}\n\n### cypher query\n```cypher\n{query}\n```\n\n")

    with open('/home/raynier/Development/workspaces/fullstack/vibes/TOWER_WORKSPACE/scratch/validation_rules.md', 'w') as f:
        f.write("".join(new_content))

if __name__ == "__main__":
    clean_and_regenerate()
