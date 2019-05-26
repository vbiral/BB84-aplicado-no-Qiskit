nome_arquivo = 'resultado' + str(datetime.now()) + '.csv'
nome_arquivo.replace(' ', '')
with open(nome_arquivo, 'w',newline='') as csvFile:
    fields=['qubits','qubit_errors_calculated','qubit_errors_measured']
    writer = csv.writer(csvFile)
    writer.writerow(fields)
    for k in qubit_errors_calculated.keys():
        writer.writerow([k, qubit_errors_calculated[k], qubit_errors_measured[k]])
    
    csvFile.close()