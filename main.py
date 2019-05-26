"""
Joshua Mwandu, Max Taylor II
BB-84 Protocol Simulator
Fall 2016 Mathematics Research Project
4 December, 2016

Victor Placido, Vinicius Fernandes
Simulação BB-84 utilizando o Qiskit
18 Abril, 2019

"""
#Versão com os simuladores 
import numpy as np
import seaborn as sns
import csv
import time
from datetime import datetime
from random import randint, random, sample
from math import ceil, log, sqrt
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister
from qiskit import Aer, BasicAer, IBMQ, execute
from qiskit.providers.aer import noise
from tqdm import tqdm

Alice = {'generatedBits':[], 'chosenBases':[], 'siftedBits':[], 'siftedBases':[], 'finalKey':[]}
Bob = {'measuredBits':[], 'chosenBases':[], 'siftedBits':[], 'siftedBases':[], 'finalKey':[]}
Eve = {'measuredBits':[], 'chosenBases':[], 'siftedBits':[], 'siftedBases':[]}
circ = QuantumCircuit()
correct_basis_indices = []
BITSIZE = 0
qber_calculated = 0.0
qber_actual = 0.0

gate_times = [
    ('u1', None, 0), ('u2', None, 100), ('u3', None, 200),
    ('cx', [1, 0], 678), ('cx', [1, 2], 547), ('cx', [2, 3], 721),
    ('cx', [4, 3], 733), ('cx', [4, 10], 721), ('cx', [5, 4], 800),
    ('cx', [5, 6], 800), ('cx', [5, 9], 895), ('cx', [6, 8], 895),
    ('cx', [7, 8], 640), ('cx', [9, 8], 895), ('cx', [9, 10], 800),
    ('cx', [11, 10], 721), ('cx', [11, 3], 634), ('cx', [12, 2], 773),
    ('cx', [13, 1], 2286), ('cx', [13, 12], 1504), ('cx', [], 800)
]

IBMQ.load_accounts()
backend_sim = Aer.get_backend('qasm_simulator')
device = IBMQ.get_backend('ibmq_16_melbourne')
properties = device.properties()
coupling_map = device.configuration().coupling_map
noise_model = noise.device.basic_device_noise_model(properties, gate_times=gate_times)

def colhe_resposta(tipo='int',texto='Resposta? ', binario=True, limite_minimo=0, limite_maximo=1):
    '''
    FUNÇÃO PARA COLHER E VALIDAR RESPOSTAS DE USUARIOS
    INPUTS:
        TIPO -> TIPOS ACEITOS -> INT, STR E FLOAT
        TEXTO -> TEXTO QUE SERÁ EXIBIDO PARA O USUÁRIO
        BINARIO -> A RESPOSTA DEVE SER BINARIA? (VALIDO PARA OS TIPOS INT E STR)
        LIMITA_MINIMO -> LIMITE MINIMO DA RESPOSTA. VALIDO PARA O TIPO FLOAT
        LIMITA_MAXIMO -> LIMITE MAXIMO DA RESPOSTA. VALIDO PARA O TIPO FLOAT
    '''
    saida=''
    if(limite_maximo < limite_minimo):
        return saida
    while((not isinstance(saida,eval(tipo))) or saida == ''):
        try:
            saida = eval(tipo + '(input(texto))')
            if(tipo != 'float' and binario==True and tipo=='str'):
                if(binario):
                    if((saida != 0 and saida != 1) and (saida != 's' and saida != 'n' and saida != 'S' and saida != 'N')):
                        raise ValueError('')
            else:
                if(saida > limite_maximo or saida < limite_minimo):
                    raise ValueError('')
        except:
            saida=''
            print('FORMATO DE ENTRADA ERRADO!!!!\n')
    return saida

#Reseta tudo
def clear_data():
    global Alice, Bob, Eve, correct_basis_indices
    Alice = {'generatedBits':[], 'chosenBases':[], 'siftedBits':[], 'siftedBases':[], 'finalKey':[]}
    Bob = {'measuredBits':[], 'chosenBases':[], 'siftedBits':[], 'siftedBases':[], 'finalKey':[]}
    Eve = {'measuredBits':[], 'chosenBases':[], 'siftedBits':[], 'siftedBases':[]}
    correct_basis_indices = []

#Passo 1 do protocolo
def step1(circ, q, c, bit_size):
    temp_bit_list = []
    temp_basis_list = []

    for i in range(0, bit_size):
        random_bit = randint(0,1)
        random_basis = randint(0,1)

        temp_bit_list.append(random_bit)

        if (random_bit == 1):
            circ.x(q[i])
            
        if (random_basis == 0):
            temp_basis_list.append('X')
        elif (random_basis == 1):
            temp_basis_list.append('Z')
            circ.h(q[i])

    Alice['generatedBits'] = temp_bit_list
    Alice['chosenBases'] = temp_basis_list

#Passo 2 e 3 do protocolo
def step2_3(circ, q, c, bit_size, com_erro, computador_real, tem_eve):
    
    if(tem_eve):
        #Adiciono a leitura da Eve
        temp_bit_list_Eve = []
        temp_basis_list_Eve = []
        global device

        for i in range(0, bit_size):
            random_basis = randint(0,1)
            if (random_basis == 0):
                temp_basis = 'X'
            elif (random_basis == 1):
                temp_basis = 'Z'
                circ.h(q[i])

            temp_basis_list_Eve.append(temp_basis)

        #Realizo a medição da Eve
        circ.barrier(q)
        circ.measure(q,c)

        if(com_erro==1):
            result = execute(circ,
                      backend_sim,
                      noise_model=noise_model,
                      coupling_map=coupling_map,
                      basis_gates=noise_model.basis_gates,
                      shots=1).result()
        else:
            result = execute(circ, backend_sim, shots=1).result()
        
        counts = result.get_counts(circ)
        resultado = list(counts.keys())[0] 
    
        for i in str(resultado)[::-1]:
            temp_bit_list_Eve.append(int(i))

        Eve['measuredBits'] = temp_bit_list_Eve
        Eve['chosenBases'] = temp_basis_list_Eve
    
    #Realizo os mesmos passos anteriores para o Bob
    temp_bit_list_Bob = []
    temp_basis_list_Bob = []

    for i in range(0, bit_size):
        random_basis = randint(0,1)
        if (random_basis == 0):
            temp_basis = 'X'
        elif (random_basis == 1):
            temp_basis = 'Z'
            circ.h(q[i])

        temp_basis_list_Bob.append(temp_basis)
        
    #Realizo a medição do Bob    
    circ.barrier(q)
    circ.measure(q,c)

    if(computador_real==1):
        result = execute(circ,
                        device,
                        shots=1024,
                        max_credits=1).result()
    else:
        if(com_erro==1):
            result = execute(circ,
                        backend_sim,
                        noise_model=noise_model,
                        coupling_map=coupling_map,
                        basis_gates=noise_model.basis_gates,
                        shots=1).result()
        else:
            result = execute(circ, backend_sim, shots=1).result()
    
    counts = result.get_counts(circ)
    resultado = list(counts.keys())[0] 

    for i in str(resultado)[::-1]:
        temp_bit_list_Bob.append(int(i))

    Bob['measuredBits'] = temp_bit_list_Bob
    Bob['chosenBases'] = temp_basis_list_Bob

#Passo 4 e 5 do protocolo
def step4_5(bit_size):
    for i in range(0, bit_size):
        if (Alice['chosenBases'][i] == Bob['chosenBases'][i]):
            correct_basis_indices.append(i)

#Passo 6 do protocolo:     
def step6(bit_size, tem_eve):

    for i in range(bit_size):
        if(Alice['chosenBases'][i]==Bob['chosenBases'][i]):
            Alice['siftedBases'].append(Alice['chosenBases'][i])
            Alice['siftedBits'].append(Alice['generatedBits'][i])

            Bob['siftedBases'].append(Bob['chosenBases'][i])
            Bob['siftedBits'].append(Bob['measuredBits'][i])

        if(tem_eve == 1):
            if(Alice['chosenBases'][i]==Eve['chosenBases'][i]):
                Eve['siftedBases'].append(Eve['chosenBases'][i])
                Eve['siftedBits'].append(Eve['measuredBits'][i])
    
#Passo 7 do protocolo
def step7(reveal_size):
    #Calcula a taxa de erro de Qubits
    #Tamanho da amostra a ser compartilhada em canal público
    global BITSIZE
    reveal_size = round(reveal_size * len(Alice['siftedBits']))
    BITSIZE = reveal_size

    #Lista dos indices que serão revelados
    random_indicies = sorted(sample(range(len(Alice['siftedBits'])), reveal_size))
    
    #Lista de amostras em que as bases batem
    random_sample_alice = [Alice['siftedBits'][i] for i in random_indicies]
    random_sample_bob = [Bob['siftedBits'][i] for i in random_indicies]
    
    #Taxa de erro da amostra
    incorrect = 0
    
    for i in range(reveal_size):
        if (random_sample_alice[i] != random_sample_bob[i]):
            incorrect += 1
    
    global qber_calculated
    if(reveal_size != 0):
        qber_calculated = 1.0*incorrect / reveal_size
    else:
        qber_calculated = 1

    #Taxa de erro global
    final_bits_alice = []
    final_bits_bob = []
    
    for i in range(len(Alice['siftedBits'])):
        if (i not in random_indicies):
            final_bits_alice.append(Alice['siftedBits'][i])
            final_bits_bob.append(Bob['siftedBits'][i])
    
    Alice['finalKey'] = final_bits_alice
    Bob['finalKey'] = final_bits_bob
    
    incorrect = 0
    
    for i in range(len(final_bits_alice)):
        if (final_bits_alice[i] != final_bits_bob[i]):
            incorrect += 1
    
    global qber_actual
    if(len(final_bits_alice) != 0):
        qber_actual = 1.0*incorrect / len(final_bits_alice)
    else:
        qber_actual = 1

#formula for secure key rate
#takes decimal from 0 to 1, returns the secure key rate as a decimal from 0 to 1
def secureKeyRate(x):
    if(x == 1):
        return 0
    if(x == 0):
        return 1
    return ((-x)*log(x, 2) - (1-x)*log(1-x, 2))
    
#Apresentação para mostrar detalhadamente o processo do BB84
def detailedPresentation(bit_size, tem_eve, reveal_size, com_erro, computador_real):
    global BITSIZE
    BITSIZE = bit_size

    clear_data()
    circ = QuantumCircuit()
    q = QuantumRegister(bit_size, 'q')
    c = ClassicalRegister(bit_size, 'c')
    circ.add_register(q)
    circ.add_register(c)

    print("Bem Vindo!")
    print("Esse programa ira mostrar a você o passo a passo para criar um hash seguro com o BB-84!")
    input("Pressione Enter para avançar para o Passo 1...\n")
    
    print("Passo 1: Alice prepara uma série de qubits e seleciona aleatoriamente sua polarização e base")
    step1(circ, q, c, bit_size)
    print("Qubits e bases de Alice:")
    print(Alice['generatedBits'])
    print(Alice['chosenBases'])

    input("Pressione Enter para ir para o Passo 2...\n")
    print("Passo 2: Alice envia cada Qubit para Bob (Que pode ser interceptado por Eve)")
    print("Passo 3: Bob lê os qubits enviados e guarda os resultados")

    step2_3(circ, q, c, bit_size, com_erro, computador_real, tem_eve)
    print("Bits e Bases da Eve:")
    print(Eve['measuredBits'])
    print(Eve['chosenBases'], "\n")
    print("Bits e Bases do Bob:")
    print(Bob['measuredBits'])
    print(Bob['chosenBases'])
    input("Pressione Enter para ir para o Passo 4...\n")
    
    print("Passo 4: Bob explicita para Alice quais bases ele utilizou")
    print("Passo 5: Alice fala quais bases ela utilizou na codificacao")
    step4_5(bit_size)
    print("Indices na quais Alice e Bob escolheram as mesmas bases:")
    print([i+1 for i in correct_basis_indices])
    input("Pressione Enter para ir para o Passo 6...\n")
    
    print("Passo 6: Alice e Bob desconsideram os qubits na qual suas bases nao batem (Eve faz o mesmo)")
    step6(bit_size, tem_eve)
    print("Bits e Bases que sobraram da Alice:")
    print(Alice['siftedBits'])
    print(Alice['siftedBases'], "\n")
    print("Bits e Bases que sobraram de Bob:")
    print(Bob['siftedBits'])
    print(Bob['siftedBases'], "\n")
    print("Bits e Bases que sobraram da Eve:")
    print(Eve['siftedBits'])
    print(Eve['siftedBases'], "\n")
    print("Tamanho das bases: ", len(Alice['siftedBits']))
    print("Porcentagem da redução: " + str((BITSIZE-len(Alice['siftedBits']))/BITSIZE*100) + "%")
    input("Pressione Enter para ir para o Passo 7...\n")
    
    print("Passo 7: Alice e Bob concordam em divulgar publicamente parte dos qubits medidos, de forma a calcular a taxa de erro.")
    step7(reveal_size)
    print("A taxa de erro calculada eh de: " + str(100*qber_calculated) + "%")
    print("A taxa de erro real eh de: " + str(100*qber_actual) + "%")
    print("A taxa de segurança da chave calculada eh de: " + str(100*secureKeyRate(qber_calculated)) + "%")
    print("A taxa de segurança da chave real eh de: " + str(100*secureKeyRate(qber_actual)) + "%")
    input("Pressione Enter para terminar a apresentacao...\n")

#Simulação rapida do BB84, apenas cospe as taxas de erro
def quickPresentation(bit_size, com_erro, tem_eve, reveal_size, computador_real):

    clear_data()
    circ = QuantumCircuit()
    q = QuantumRegister(bit_size, 'q')
    c = ClassicalRegister(bit_size, 'c')
    circ.add_register(q)
    circ.add_register(c)

    step1(circ, q, c, bit_size)
    step2_3(circ, q, c, bit_size, com_erro, computador_real, tem_eve)
    print("Bits e Bases da Eve:")
    print(Eve['measuredBits'])
    print(Eve['chosenBases'], "\n")
    step4_5(bit_size)
    step6(bit_size,tem_eve)
    step7(reveal_size)
    print("A taxa de erro calculada eh de: " + str(100*qber_calculated) + "%")
    print("A taxa de erro real eh de: " + str(100*qber_actual) + "%")
    print("A taxa de segurança da chave calculada eh de: " + str(100*secureKeyRate(qber_calculated)) + "%")
    print("A taxa de segurança da chave real eh de: " + str(100*secureKeyRate(qber_actual)) + "%")
    input("Pressione Enter para terminar a apresentacao...\n")

#Teste de stress do BB84
def stresstest(quantidade_minima, bit_size, com_erro, tem_eve, reveal_size, nome_arquivo, computador_real, vezes = 30):
    qubit_errors_calculated = dict()
    qubit_errors_measured = dict()
    reveal_size_dict = dict()
    tempo_execucao = dict()
    for i in tqdm(range(quantidade_minima-1, bit_size, 1)):
        qubit_errors_calculated_aux=0
        qubit_errors_measured_aux=0
        tempo_execucao_aux = 0
        reveal_size_aux = 0
        for j in range(vezes):
            inicio = time.time()
            clear_data()
            circ = QuantumCircuit()
            q = QuantumRegister(i+1, 'q')
            c = ClassicalRegister(i+1, 'c')
            circ.add_register(q)
            circ.add_register(c)

            step1(circ, q, c, i+1)
            step2_3(circ, q, c, i+1, com_erro, computador_real, tem_eve)
            step4_5(i+1)
            step6(i+1, tem_eve)
            step7(reveal_size)
            qubit_errors_calculated_aux = qubit_errors_calculated_aux + qber_calculated
            qubit_errors_measured_aux = qubit_errors_measured_aux + qber_actual
            
            global BITSIZE
            reveal_size_aux = reveal_size_aux + BITSIZE
            fim = time.time()
            tempo_execucao_aux = tempo_execucao_aux + (fim-inicio) 
        #print(Alice)
        #print(Bob)
        #print(Eve)
        #print(circ)
    
        qubit_errors_calculated[str(i+1)] = 1.0*(qubit_errors_calculated_aux/vezes)
        qubit_errors_measured[str(i+1)] = 1.0*(qubit_errors_measured_aux/vezes)
        tempo_execucao[str(i+1)] = 1.0*(tempo_execucao_aux/vezes)
        reveal_size_dict[str(i+1)] = 1.0*(reveal_size_aux/vezes)
    
    nome_arquivo = nome_arquivo + '.csv'
    with open(nome_arquivo, 'w',newline='') as csvFile:
        fields=['qubits','qubit_errors_calculated','qubit_errors_measured','quantidade_qubits_revelados','tempo_execucao_1']
        writer = csv.writer(csvFile)
        writer.writerow(fields)
        for k in qubit_errors_calculated.keys():
            writer.writerow([k, qubit_errors_calculated[k],
                                qubit_errors_measured[k],
                                reveal_size_dict[k],
                                tempo_execucao[k]])
    
    csvFile.close()

    print('###############################################')

#Comeca aqui
if __name__ == "__main__":
    done = False
    while (not done):
        print("O que você quer fazer?\n")
        print("1: Rodar uma simulação detalhada?")
        print("2: Rodar uma simulação simples?")
        print("3: Teste de Stress?")
        print("4: Sair")
        userInput = input("Escolha uma opção: ")
        
        if (userInput == '1'):
            userInput =  colhe_resposta(tipo='int',
                                        texto='\nQuantos Qubits utilizar? ',
                                        binario=False,
                                        limite_minimo=1,
                                        limite_maximo=50)
            tem_eve = colhe_resposta(tipo='int',
                                    texto='\nDeseja que a mensagem seja interceptada?(1/0) ',
                                    binario=True)
            reveal_size = colhe_resposta(tipo='float',
                                         texto="\nPorcentagem utilizada na comparacao?(Em valor absoluto) ",
                                         binario=False)
            com_erro = colhe_resposta(tipo='int',
                                      texto='\nSimulação com erro?(1/0) ',
                                      binario=True)
            computador_real = colhe_resposta(tipo='int',
                                             texto='\nRodar em um computador quântico real?(1/0) ',
                                             binario=True)

            print('###############################################')
            print('RESUMO DA OPERACAO:')
            print('Quantidade de qubits = ' + str(userInput))
            print('Simulador escolhido = ' + 'Qiskit')
            print('Simulação com erro = ' + str(com_erro))
            print('Tem invasor = ' + str(tem_eve))
            print('Quantidade da mensagem que sera revelada = ' + str(reveal_size))
            print('###############################################')
            
            detailedPresentation(int(userInput), tem_eve, reveal_size, com_erro, computador_real)
        
        elif (userInput == '2'):
            userInput =  colhe_resposta(tipo='int',
                                        texto='\nQuantos Qubits utilizar? ',
                                        binario=False,
                                        limite_minimo=1,
                                        limite_maximo=50)
            tem_eve = colhe_resposta(tipo='int',
                                    texto='\nDeseja que a mensagem seja interceptada?(1/0) ',
                                    binario=True)
            reveal_size = colhe_resposta(tipo='float',
                                         texto="\nPorcentagem utilizada na comparacao?(Em valor absoluto) ",
                                         binario=False)
            com_erro = colhe_resposta(tipo='int',
                                      texto='\nSimulação com erro?(1/0) ',
                                      binario=True)
            computador_real = colhe_resposta(tipo='int',
                                             texto='\nRodar em um computador quântico real?(1/0) ',
                                             binario=True)

            print('###############################################')
            print('RESUMO DA OPERACAO:')
            print('Quantidade de qubits = ' + str(userInput))
            print('Simulador escolhido = ' + 'Qiskit')
            print('Simulação com erro = ' + str(com_erro))
            print('Tem invasor = ' + str(tem_eve))
            print('Quantidade da mensagem que sera revelada = ' + str(reveal_size))
            print('###############################################')

            quickPresentation(int(userInput), com_erro, tem_eve, reveal_size, computador_real)
        
        elif (userInput == '3'):
            quantidade_minima =  colhe_resposta(tipo='int',
                                                texto='\nQuantidade de Qubits mínima? ',
                                                binario=False,
                                                limite_minimo=1,
                                                limite_maximo=50)
            userInput =  colhe_resposta(tipo='int',
                                        texto='\nQuantidade de Qubits máxima? ',
                                        binario=False,
                                        limite_minimo=1,
                                        limite_maximo=50)
            
            #TRECHO A SER IMPLEMENTADO
            #print('\nEscolha os simuladores:')
            #print("1: Qiskit")
            #print("OBS: Alguns simuladores suportam até o máximo de 24 Qubits")
            #simulators = input("Qual simulador utilizar? ")
            simulators=1

            tem_eve = colhe_resposta(tipo='int',
                                    texto='\nDeseja que a mensagem seja interceptada?(1/0) ',
                                    binario=True)
            reveal_size = colhe_resposta(tipo='float',
                                    texto="\nPorcentagem utilizada na comparacao?(Em valor absoluto) ",
                                    binario=False)
            vezes = colhe_resposta(tipo='int',
                                    texto='\nQuantidade de vezes por simulação? ',
                                    binario=False,
                                    limite_minimo=1,
                                    limite_maximo=1000)
            com_erro = colhe_resposta(tipo='int',
                                      texto='\nSimulação com erro?(1/0) ',
                                      binario=True)
            computador_real = colhe_resposta(tipo='int',
                                             texto='\nRodar em um computador quântico real?(1/0) ',
                                             binario=True)

            nome_arquivo = input('\nNome do arquivo de saida? ')
            print('###############################################')
            print('RESUMO DA OPERACAO:')
            print('Quantidade minima de qubits = ' + str(quantidade_minima))
            print('Quantidade maxima de qubits = ' + str(userInput))
            print('Quantidade de vezes por qubit = ' + str(vezes))
            print('Simulador escolhido = ' + 'Qiskit')
            print('Simulação com erro = ' + str(com_erro))
            print('Tem invasor = ' + str(tem_eve))
            print('Quantidade da mensagem que sera revelada = ' + str(reveal_size))
            print('Nome do arquivo de saida = ' + nome_arquivo + '.csv')
            print('###############################################')    
            stresstest(quantidade_minima,
                       int(userInput),
                       com_erro,
                       tem_eve,
                       reveal_size,
                       nome_arquivo,
                       computador_real,
                       vezes)
        
        elif (userInput == '4'):
            done = True
                        
    print("Tchau!")