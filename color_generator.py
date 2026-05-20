import random

def generate_N_HSV_colors(N):
    """
    Code inspired by: https://stackoverflow.com/a/470747, but in case for HSV (H in [0,360[, S and V in [0,1])
    """
    colors = []
    for i in range(0,360*N,360):
        color = []
        color.append(i/N)
        color.append(random.random())
        color.append(random.random())
        colors.append(color)
    return colors

def HSV_to_RGB(HSV):
    """
    Code based on: https://www.rapidtables.com/convert/color/hsv-to-rgb.html
    """

    C = HSV[1] * HSV[2]
    X = C * (1-abs((HSV[0]/60)%2 - 1))
    m = HSV[1]-C
    R = 0
    G = 0
    B = 0
    if HSV[0] >= 0 and HSV[0] < 60:
        R = C
        G = X
    elif HSV[0] >= 60 and HSV[0] < 120:
        R = X
        G = C
    elif HSV[0] >= 120 and HSV[0] < 180:
        G = C
        B = X
    elif HSV[0] >= 180 and HSV[0] < 240:
        G = X
        B = C
    elif HSV[0] >= 240 and HSV[0] < 300:
        R = X
        B = C
    elif HSV[0] >= 300 and HSV[0] < 360:
        R = C
        B = X
    color = (R+m,G+m,B+m)
    return color

def generate_N_RGB_colors(N):
    """
        First part from: https://stackoverflow.com/a/68414642
    """
    colors = []
    try:
        from distinctipy import distinctipy
        colors = distinctipy.get_colors(N)
    except ModuleNotFoundError:
        HSV_colors = generate_N_HSV_colors(N)
        for i in range(N):
            colors.append(HSV_to_RGB(HSV_colors[i]))
    return colors

def main():
    generation = generate_N_HSV_colors(10)
    print(HSV_to_RGB(generation[0]))


if __name__ == "__main__":
    main()