import cv2
import numpy as np

cam = cv2.VideoCapture(1)


while True:
    # retorna exatamente o que a camera estava vendo no instante que a funçao foi chamada
    # em formato de matriz da numpy(MatLike)
    sucess, frame = cam.read()




    # para reduzir o ruido da imagem
    # dependendo podemos usar billinearFiltering( pois mantem as bordas mais "afiadas")
    blur = cv2.GaussianBlur(frame, (5, 5), 0)

    # encontra bordas a usando gradiente e binariza a imagem
    # valormin: qualquer valor abaixo não é considerado uma borda
    # valormax: qualquer valor acima dele é considerado uma borda
    # valoresintermediarios que estiverem conectados a um valor max sao considerados bordas
    # L2gradient: quando True usa um algoritmo mais preciso
    # provavelmente precisara de calibração para cada camera

    raw_contours = cv2.Canny(blur, 50, 100, L2gradient=True)
    
    # so pega os contornos externos, forma os contornos somente com os pontos essenciais
    contours, hierarchy = cv2.findContours(
        raw_contours, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    img_contours = np.uint8(np.zeros((frame.shape[0],frame.shape[1])))

    sel_contours=[]
    max=0
    for contour in contours:
        if contour.shape[0]>max:
            sel_contours=contour
            max=contour.shape[0]
    #print(sel_contours)

    #NUMBER OF CONTOURS (OLNY ORDER) YOU WANT TO 
    #sel_contours.append(contours[0])
    #sel_contours.append(contours[1])
    
    cv2.drawContours(img_contours, sel_contours, -1, (255,255,255), 1)
    area = cv2.contourArea(sel_contours)
    
    #print text accurately in the window
    font                   = cv2.FONT_HERSHEY_SIMPLEX
    bottomLeftCornerOfText = (10,500)
    fontScale              = 1
    fontColor              = (255,255,255)
    thickness              = 1
    lineType               = 2

    cv2.putText(img_contours,f'{area}pixels', 
    bottomLeftCornerOfText, 
    font, 
    fontScale,
    fontColor,
    thickness,
    lineType)
    # mostra o frame atual



    # para cada contorno
    # usado o enumerate pois assim teremos os indices caso quisermos filtra o primeiro
    # é util principalmente quando usado a função threshold ao inves de canny para binarizar
    # ja que no threshold geralmente ele detecta o primero contorno como a propria imagem
    '''
    for i, contour in enumerate(contours):
        # calcula a area em pixels a partir do contorno (precisao muito alta)
        area = cv2.contourArea(contour)
        print(area)
        # if area < x : podemos usar isso para filtrar areas
    '''
    
    # se o unicode da key apertada for igual ao unicode da letra q
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cv2.destroyAllWindows()
