content = open('app/routers/admin_users.py','r',encoding='utf-8').read()
old = '''    csv_reader = csv.reader(io.StringIO(content_str))
    rows = list(csv_reader)'''
new = '''    # Auto-detect delimiter (tab or comma)
    sample = content_str[:500]
    delimiter = '\\t' if '\\t' in sample else ','
    csv_reader = csv.reader(io.StringIO(content_str), delimiter=delimiter)
    rows = list(csv_reader)'''
content = content.replace(old, new)
old2 = '''            badge = row[0].strip()
            name = row[1].strip()
            department = row[2].strip() if len(row) > 2 else None'''
new2 = '''            badge = row[0].strip()
            name = row[1].strip()
            department = row[2].strip() if len(row) > 2 else None
            # Skip header rows
            if badge.lower() == 'badge' or not badge.isdigit() and not badge.replace('-','').isdigit():
                if not any(c.isdigit() for c in badge):
                    continue'''
content = content.replace(old2, new2)
open('app/routers/admin_users.py','w',encoding='utf-8').write(content)
print('Done!')
