def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def give_solution(act_temp, wind, rain, gender, age):
    feel_temp = 0
    int(act_temp)
    if rain == "Yes":
        feel_temp += 2
    if wind == "Strong":
        feel_temp += 2
    temp = act_temp + feel_temp
    if temp > 26:
        if gender == "Male":
            if age <= 30:
                recommend = "1-1-1"
            elif 30 < age <= 45:
                recommend = "1-2-1"
            elif 45 < age:
                recommend = "1-3-1"

        elif gender == "Female":
            if age <= 30:
                recommend = "2-1-1"
            elif 30 < age <= 45:
                recommend = "2-2-1"
            elif 45 < age:
                recommend = "2-3-1"
    elif 23 < temp <= 26:
        if gender == "Male":
            if age <= 30:
                recommend = "1-1-2"
            elif 30 < age <= 45:
                recommend = "1-2-2"
            elif 45 < age:
                recommend = "1-3-2"
        elif gender == "Female":
            if age <= 30:
                recommend = "2-1-2"
            elif 30 < age <= 45:
                recommend = "2-2-2"
            elif 45 < age:
                recommend = "2-3-2"
    elif 20 < temp <= 23:
        if gender == "Male":
            if age <= 30:
                recommend = "1-1-3"
            elif 30 < age <= 45:
                recommend = "1-2-3"
            elif 45 < age:
                recommend = "1-3-3"
        elif gender == "Female":
            if age <= 30:
                recommend = "2-1-3"
            elif 30 < age <= 45:
                recommend = "2-2-3"
            elif 45 < age:
                recommend = "2-3-3"
    elif 17 < temp <= 20:
        if gender == "Male":
            if age <= 30:
                recommend = "1-1-4"
            elif 30 < age <= 45:
                recommend = "1-2-4"
            elif 45 < age:
                recommend = "1-3-4"

        elif gender == "Female":
            if age <= 30:
                recommend = "2-1-4"
            elif 30 < age <= 45:
                recommend = "2-2-4"
            elif 45 < age:
                recommend = "2-3-4"

    elif 14 < temp <= 17:
        if gender == "Male":
            if age <= 30:
                recommend = "1-1-5"
            elif 30 < age <= 45:
                recommend = "1-2-5"
            elif 45 < age:
                recommend = "1-3-5"

        elif gender == "Female":
            if age <= 30:
                recommend = "2-1-5"
            elif 30 < age <= 45:
                recommend = "2-2-5"
            elif 45 < age:
                recommend = "2-3-5"
    elif temp <= 14:
        if gender == "Male":
            if age <= 30:
                recommend = "1-1-6"
            elif 30 < age <= 45:
                recommend = "1-2-6"
            elif 45 < age:
                recommend = "1-3-6"
        elif gender == "Female":
            if age <= 30:
                recommend = "2-1-6"
            elif 30 < age <= 45:
                recommend = "2-2-6"
            elif 45 < age:
                recommend = "2-3-6"
    return recommend+'.jpg'
