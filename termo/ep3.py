"""
  AO PREENCHER ESSE CABEÇALHO COM O MEU NOME E O MEU NÚMERO USP, 
  DECLARO QUE SOU RESPONSÁVEL POR ESSE PROGRAMA. 
  TODAS AS PARTES ORIGINAIS DESSE EXERCÍCIO PROGRAMA (EP) FORAM 
  DESENVOLVIDAS E IMPLEMENTADAS POR MIM SEGUINDO AS INSTRUÇÕES
  DESSE EP E PORTANTO NÃO CONSTITUEM DESONESTIDADE ACADÊMICA
  OU PLÁGIO.  
  DECLARO TAMBÉM QUE SOU RESPONSÁVEL POR TODAS AS CÓPIAS DESSE 
  PROGRAMA E QUE EU NÃO DISTRIBUI OU FACILITEI A SUA DISTRIBUIÇÃO. 
  ENTENDO QUE EPS SEM ESTE CABEÇALHO NÃO SERÃO CORRIGIDOS E,
  AINDA ASSIM, PODERÃO SER PUNIDOS POR DESONESTIDADE ACADÊMICA.

  Nome : Lucas Toshioka Tenório
  NUSP : 16885230

  """
  
import random

MAX_TENTATIVAS = 6
NUM_LETRAS = 5



def main():
    ' Implementa mecanismo principal do jogo. '   
    # pede opção de lingua
    lingua = ''
    while lingua != 'P' and lingua != 'I':
        lingua = input("Qual o idioma (I para inglês ou P para português)? ")
    
    # carrega lista de palavras do arquivo correspondente
    if lingua == 'P':
        lista_palavras = cria_lista_palavras("palavras.txt")
    elif lingua =='I':
        lista_palavras = cria_lista_palavras("words.txt")

    # sorteia uma palavra da lista
    palavra = lista_palavras[random.randint(0,len(lista_palavras)-1)]
    num_tentativas = 0
    lista_tentativas = []
    ganhou = False
    teclado =  inicializa_teclado()

    imprime_teclado(teclado)

    while num_tentativas < MAX_TENTATIVAS and not ganhou:
        #verifica se a tentativa é válida
        valida = False
        chute=""
        while not valida:
            chute=input("Digite a palavra: ")
            if len(chute)!=NUM_LETRAS or tratar_palavra(chute) not in tratar_lista(lista_palavras):
                print("Palavra inválida!")
            else:
                valida = True
        #inicializa a lista da tentativa
        tentativa=[]
        tentativa.append(chute)
        #checa a tentativa e armazena o resultado
        marcas = [0]*NUM_LETRAS
        checa_tentativa(palavra, chute, marcas)
        tentativa.append(marcas[:])
        lista_tentativas.append(tentativa[:])
        #atualiza o teclado e o número de tentativas
        atualiza_teclado(chute, marcas, teclado)
        num_tentativas+=1
        #imprime o resultado
        imprime_resultado(lista_tentativas)
        #verifica se o resultado está correto
        if tratar_palavra(chute) == tratar_palavra(palavra):
            ganhou = True
        else:
            imprime_teclado(teclado)


    if ganhou: 
       print("PARABÉNS!")
    else: 
       print("Que pena... A palavra era",palavra,".")



def cria_lista_palavras(nome_arquivo):
    ''' recebe uma string com o nome do arquivo e devolve uma lista
        contendo as palavras do arquivo'''
    lista = []
    palavras = open(nome_arquivo)
    for linha in palavras:
        lista.append(linha.strip())
    palavras.close()
    return lista



def inicializa_teclado():
    '''
    Devolve a lista com as teclas na ordem.
    As letras que aparecem nos chutes e que não estão no teclado são substtuídas por ' '.
    '''
    
    teclado = [['q','w','e','r','t','y','u','i','o','p'],
               ['a','s','d','f','g','h','j','k','l'],
               ['z','x','c','v','b','n','m']]
    return teclado

        

def checa_tentativa(palavra,chute,marca):
    ''' Recebe a `palavra` secreta e o `chute` do usuario e modifica as
     `marca`s para indicar acertos e erros. A lista `marca` deve conter o 
     valor 1 (verde) se a letra correspondente em `chute` ocorre na mesma posicao
     em `palavra` (letra certa no lugar certo), deve conter 2 se a letra 
     em `chute` ocorre em outra posicao em `palavra` (letra certa no lugar errado),
     e deve conter 0 caso contrario. Esta funcao nao devolve valor. '''
    #remove os acentos da palavra pra evitar redundâncias
    palavra = tratar_palavra(palavra)
    chute = tratar_palavra(chute)
    for i in range(len(palavra)):
        if chute[i]==palavra[i]:
            marca[i]=1
        elif chute[i] in palavra:
            marca[i]=2
        else:
            marca[i]=0



def  imprime_resultado(lista):
    ''' Recebe a lista de tentativas e imprime as tentativas,
      usando * para verde e + para amarelo. Esta funcao nao devolve valor. '''
    for tentativa in lista:
            s=""
            k=""
            #separa as letras da palavra adicionando espaço entre elas
            for i in range(len(tentativa[0])):
                s+=tentativa[0][i]
                if i!=len(tentativa[0])-1:
                    s+=" "
            print(s)
            #separa os caracteres adicionando espaço entre eles
            for j in range(len(tentativa[1])):
                if tentativa[1][j]==0:
                    k+="_"
                elif tentativa[1][j]==1:
                    k+="*"
                elif tentativa[1][j]==2:
                    k+="+"
                if k!=len(tentativa[1])-1:
                    k+=" "
            print(k)



def imprime_teclado(teclado):
    ''' Exibe o teclado com as letras possiveis. '''   
    print('-----------------------------------------')
    for linha in teclado:
        for letra in linha:
            print(letra, end = ' ')
        print()
    print('-----------------------------------------')
            


def atualiza_teclado(chute,marca,teclado):
    ''' Modifica teclado para que as letras marcadas como inexistentes
	 no chute sejam substituidas por espacos. Esta funcao nao devolve valor.'''
    #remove os acentos da palavra pra evitar redundâncias
    chute = tratar_palavra(chute)
    for i in range(len(chute)):
        if marca[i]==0:
            #itera pelo teclado procurando a mesma letra
            for k in range(len(teclado)):
                for l in range(len(teclado[k])):
                    if chute[i]==teclado[k][l]:
                        teclado[k][l]=" "



def tratar_palavra(palavra):
    ''' Recebe uma string e devolve essa string
    sem acentos e/ou caracteres especiais. '''
    palavra = palavra.lower()
    nova_palavra = ""
    a = ["á", "à", "ã", "â"]
    e = ["é", "ê"]
    i = ["í"]
    o = ["ó", "ô", "õ"]
    u = "ú"
    c = "ç"
    for letra in palavra:
        if letra in a:
            nova_palavra+="a"
        elif letra in e:
            nova_palavra+="e"
        elif letra in i:
            nova_palavra+="i"
        elif letra in o:
            nova_palavra+="o"
        elif letra == u:
            nova_palavra+="u"
        elif letra == c:
            nova_palavra+="c"
        else:
            nova_palavra+=letra
    return nova_palavra



def tratar_lista(lista):
    ''' Recebe uma lista de strings e
    devolve essa lista com as palavras
    sem acentos e/ou caracteres especiais. '''
    nova_lista=[]
    for i in lista:
        nova_lista.append(tratar_palavra(i))
    return nova_lista



if __name__ == "__main__":
    main()
