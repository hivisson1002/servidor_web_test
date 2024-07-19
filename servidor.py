"""
Uso: ./start_server -p(multi process)? -t(multi thread)? -w? <workers>

Isso criará um servidor HTTP ouvindo em LOCALHOST:PORT
"""

import socket
import multiprocessing
import threading
import os
import time
import argparse

# Número máximo de conexões na fila do socket
BACKLOG = 5

# Tamanho máximo dos dados lidos de um socket
MAX_DATA_SIZE = 1024

# Estilo de codificação
STYLE = "utf-8"

# Localhost
LOCALHOST = "127.0.0.1"

# Porta para iniciar o servidor
PORT = 2000

# Número de processos/threads de trabalho
WORKER_SIZE = 5

# Usa multi-processamento se definido como 0
USE_THREADING = 0

# Variável global de desligamento
shutdown = False

# Timeout para socket.accept()
SOCK_TIMEOUT = 2

def tarefa_cpu_intensiva():
    print("Executando tarefa intensiva de CPU")
    # Uma tarefa fictícia intensiva de CPU
    def eh_primo(n):
        if n <= 1:
            return False
        elif n == 2:
            return True
        elif n % 2 == 0:
            return False
        else:
            for i in range(3, int(n**0.5) + 1, 2):
                if n % i == 0:
                    return False
            return True

    def encontrar_primos_no_intervalo(inicio, fim):
        primos = []
        for numero in range(inicio, fim + 1):
            if eh_primo(numero):
                primos.append(numero)
        return primos

    res = encontrar_primos_no_intervalo(1, 1000000)
    print("Tarefa intensiva de CPU concluída")

def tarefa_io_intensiva():
    print("Executando tarefa intensiva de E/S")
    # Simula uma leitura de arquivo ou qualquer outra operação que requeira E/S
    time.sleep(1)
    print("Tarefa intensiva de E/S concluída")

def obter_pagina(caminho):
    # Configuração especial para testes
    if caminho == "/cpu":
        caminho = "/"
        tarefa_cpu_intensiva()

    if caminho == "/io":
        caminho = "/"
        tarefa_io_intensiva()

    WEB_DIR = "www"  # Diretório para armazenar todas as páginas web
    if caminho == "":
        return None
    if caminho == "/":
        caminho = "/index.html"

    try:
        with open(WEB_DIR + caminho, 'r') as arquivo:
            conteudo = arquivo.read()
        return conteudo
    except FileNotFoundError:
        return None

def tratar_requisicao(socket_cliente):
    dados = socket_cliente.recv(MAX_DATA_SIZE).decode(STYLE)
    linhas = dados.split('\r\n')
    if linhas:
        linha = linhas[0]
        palavras = linha.split(' ')
        caminho = "" if len(palavras) < 2 else palavras[1]
        conteudo = obter_pagina(caminho)
        codigo_resposta = "200 OK" if conteudo else "404 Not Found"
        # Cria a resposta
        resposta = f"HTTP/1.1 {codigo_resposta}\r\n\r\n"
        if conteudo:
            resposta += f"{conteudo}\r\n"
        # Responde ao cliente
        socket_cliente.sendall(resposta.encode(STYLE))

def configurar_servidor(host, port):
    """
    Retorna um socket ouvindo em (host, port)
    """
    # Cria um objeto socket
    # socket.AF_INET: indica IPv4
    # socket.SOCK_STREAM: indica TCP
    socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Permite reutilizar o endereço local ao qual o socket está vinculado.
    # Evita o erro "Endereço já em uso" que pode ocorrer se o servidor for reiniciado
    # e o socket anterior ainda estiver no estado TIME_WAIT.
    socket_servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Vincula o socket a um host e porta específicos
    # Deve reclamar se o host ou porta não forem válidos
    socket_servidor.bind((host, port))

    # Timeout é essencial para evitar espera infinita
    socket_servidor.settimeout(SOCK_TIMEOUT)

    # Começa a ouvir
    socket_servidor.listen(BACKLOG)
    print(f"Servidor ouvindo em {host}:{port}")
    return socket_servidor

def tratar_conexoes(socket_servidor):
    """
    Aceita requisições HTTP (para sempre) ouvindo no socket_servidor
    """
    print(f"Iniciando trabalhador de conexão para {socket_servidor.getsockname()},"
          f" pid: {os.getpid()}, tid: {threading.get_ident()}")
    global shutdown
    while not shutdown:
        socket_cliente = None
        try:
            # Espera por uma conexão
            # Note que accept() é thread safe
            socket_cliente, endereco_cliente = socket_servidor.accept()
            print(f"Recebeu uma nova conexão de {endereco_cliente}")
            tratar_requisicao(socket_cliente)
        except socket.timeout:
            pass
        except socket.error as e:
            if e.errno == 10035:  # WSAEWOULDBLOCK
                # Chamada não bloqueante, tente novamente mais tarde
                continue
            else:
                print(str(e))
        except SystemExit:
            print("Trabalhador terminando....")
        except Exception as e:
            print(str(e))
        finally:
            if socket_cliente:
                socket_cliente.close()
                print(f"Fechou a conexão de {endereco_cliente}")
    # Fecha a conexão (não acontecerá se o trabalhador for terminado!)
    print(f"Fechando trabalhador de conexão para: pid: {os.getpid()},"
          f" tid: {threading.get_ident()}")

def obter_argumentos():
    # ToDo: Melhorar isso para incluir host e porta também
    parser = argparse.ArgumentParser(description="Um script para iniciar um servidor HTTP básico")
    parser.add_argument("-p", "--process", action='store_true',
                        help="Flag indicando que o servidor será executado em modo multi-processo")
    parser.add_argument("-t", "--thread", action='store_true',
                        help="Flag indicando que o servidor será executado em modo multi-thread")
    parser.add_argument('-w', '--workers', type=int, help='Número de trabalhadores')
    args = parser.parse_args()
    if args.process and args.thread:
        raise ValueError("Por favor, use -p OU -t")
    return args

def main():
    host_servidor = LOCALHOST
    porta_servidor = PORT
    socket_servidor = None
    args = obter_argumentos()

    if args.thread:
        global USE_THREADING
        USE_THREADING = True
    if args.workers:
        global WORKER_SIZE
        WORKER_SIZE = args.workers

    try:
        socket_servidor = configurar_servidor(host_servidor, porta_servidor)
    except Exception as e:
        print(str(e))
        print("configurar_servidor falhou! Saindo...")
        return

    if socket_servidor is None:
        print("Socket do servidor inválido. Saindo")
        return

    trabalhadores = []

    for i in range(WORKER_SIZE):
        p = None
        if USE_THREADING:
            p = threading.Thread(target=tratar_conexoes, args=(socket_servidor,))
        else:
            p = multiprocessing.Process(target=tratar_conexoes, args=(socket_servidor,))
        trabalhadores.append(p)

    for trabalhador in trabalhadores:
        trabalhador.start()

    try:
        print(f"Main thread tid: {threading.get_ident()}")
        # Espera até que o processo principal seja manualmente encerrado
        while True:
            # Não faz nada
            pass
    except KeyboardInterrupt:
        print(f"\nSaindo devido a uma interrupção do teclado\n")
    finally:
        global shutdown
        shutdown = True
        # Fecha todos os trabalhadores
        if not USE_THREADING:
            for trabalhador in trabalhadores:
                trabalhador.terminate()

        # Espera que todos os trabalhadores terminem
        for trabalhador in trabalhadores:
            # No caso de threads, isso esperará
            # para sempre, o usuário terá que enviar
            # interrupção do teclado novamente
            # Não é ideal.
            trabalhador.join()

        print("Servidor está desligando.")
        # Fecha o socket do servidor
        if socket_servidor:
            socket_servidor.close()

if __name__ == "__main__":
    main()
