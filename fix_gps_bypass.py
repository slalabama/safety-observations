content = open('app/routers/admin_auth.py','r',encoding='utf-8').read()
old = '''    distance_miles = calculate_distance(
        request.latitude, request.longitude,
        facility.latitude, facility.longitude
    )
    
    if distance_miles > facility.radius_miles:
        raise HTTPException(
            status_code=403,
            detail=f"You are {distance_miles:.2f} miles from facility. Max allowed: {facility.radius_miles} miles."
        )'''
new = '''    # Admins bypass GPS fence
    if employee.role != 'admin':
        distance_miles = calculate_distance(
            request.latitude, request.longitude,
            facility.latitude, facility.longitude
        )
        
        if distance_miles > facility.radius_miles:
            raise HTTPException(
                status_code=403,
                detail=f"You are {distance_miles:.2f} miles from facility. Max allowed: {facility.radius_miles} miles."
            )'''
content = content.replace(old, new)
open('app/routers/admin_auth.py','w',encoding='utf-8').write(content)
print('Done:', len(content))
