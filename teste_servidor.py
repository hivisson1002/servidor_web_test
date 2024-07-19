"""
Uso: ./test_my_server -c(cpu)/-i(io) -nc? <clientes> <host> <porta>

Um script genérico para testar o desempenho de um servidor HTTP
"""

import requests
import argparse
import multiprocessing
import time

# número de requisições paralelas
CLIENTES = 5

def enviar_requisicao_http(host, porta, endpoint):
    """
    Envia uma única requisição HTTP para o servidor especificado.
    
    Args:
        host (str): Endereço do servidor.
        porta (str): Porta do servidor.
        endpoint (str): Endpoint a ser acessado (cpu ou io).
    """
    url = f"http://{host}:{porta}/{endpoint}"
    inicio = time.time()
    resposta = requests.get(url)
    fim = time.time()
    print(f"{url} - Código de Status: {resposta.status_code}, levou {(fim-inicio)*1000:.2f} ms")
    #print(resposta.text)
    #print("\n")

def enviar_requisicoes_paralelas(host, porta, endpoint):
    """
    Envia múltiplas requisições HTTP em paralelo usando processos.
    
    Args:
        host (str): Endereço do servidor.
        porta (str): Porta do servidor.
        endpoint (str): Endpoint a ser acessado (cpu ou io).
    """
    processos = []
    for i in range(CLIENTES):
        # Cria um processo para cada requisição HTTP
        p = multiprocessing.Process(target=enviar_requisicao_http, args=(host, porta, endpoint))
        processos.append(p)
    inicio = time.time()
    for processo in processos:
        processo.start()  # Inicia cada processo

    for processo in processos:
        processo.join()  # Espera cada processo terminar

    fim = time.time()
    # Note que isso inclui o tempo de criação e término do processo
    print(f"Tempo total levado {(fim-inicio)*1000:.2f} ms")

def obter_args():
    """
    Obtém e parseia os argumentos da linha de comando.
    
    Returns:
        args (Namespace): Argumentos parseados.
    """
    parser = argparse.ArgumentParser(description="Um script para testar o desempenho de um servidor genérico")
    parser.add_argument("-c", "--cpu", action='store_true',
                         help="Flag para testar o desempenho de tarefas consumidoras de CPU")
    parser.add_argument("-i", "--io", action='store_true',
                         help="Flag para testar o desempenho de tarefas consumidoras de I/O")
    parser.add_argument('-nc', '--clientes', type=int, help='Número de clientes')
    parser.add_argument("host")
    parser.add_argument("porta")
    args = parser.parse_args()
    return args

def main():
    """
    Função principal que coordena o envio de requisições com base nos argumentos fornecidos.
    """
    args = obter_args()
    endpoint = ""
    if args.cpu:
        endpoint = "cpu"
    if args.io:
        endpoint = "io"
    if args.cpu and args.io:
        raise ValueError("Não é possível testar o desempenho de CPU e I/O juntos. Por favor, use -c OU -i")
    if not (args.cpu or args.io):
        raise ValueError("Especifique se deseja testar o desempenho de CPU ou I/O. Por favor, use -c OU -i")
    if args.clientes:
        global CLIENTES
        CLIENTES = args.clientes

    enviar_requisicoes_paralelas(args.host, args.porta, endpoint)
    
if __name__ == '__main__':
    main()
