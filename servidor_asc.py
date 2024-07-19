import socket
import os
import asyncio
import threading
import aiofiles

# Número máximo de conexões na fila do socket
BACKLOG = 5

# Tamanho máximo dos dados lidos de um socket
TAMANHO_MAX_DADOS = 1024

# Estilo de codificação
ESTILO = "utf-8"

# Localhost
LOCALHOST = "127.0.0.1"

# Porta para iniciar o servidor
PORTA = 2000


async def tarefa_consumidora_de_cpu():
    # não há sentido em tornar isso assíncrono, pois
    # nunca chamará await e, portanto, não será uma
    # corrotina cooperativa!

    print("Executando tarefa consumidora de CPU")
    # uma tarefa consumidora de CPU fictícia
    n = 100
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


async def tarefa_consumidora_de_io():
    print("Executando tarefa consumidora de I/O")
    # simula uma leitura de arquivo ou qualquer outra
    # operação que requer I/O
    await asyncio.sleep(1)


async def obter_pagina(caminho):

    # configuração especial para teste
    if caminho == "/cpu":
        caminho = "/"
        await tarefa_consumidora_de_cpu()
    
    if caminho == "/io":
        caminho = "/"
        await tarefa_consumidora_de_io()

    DIR_WEB = "www" # um diretório para armazenar todas as páginas web
    if caminho == "":
        return None
    if caminho == "/":
        caminho = "/index.html"

    try:
        async with aiofiles.open(DIR_WEB + caminho, 'r') as arquivo:
            conteudo = await arquivo.read()
        return conteudo
    except FileNotFoundError as f:
        return None


async def lidar_com_requisicao(socket_cliente, endereco_cliente):
    try:
        loop = asyncio.get_event_loop()
        try:
            dados = (await loop.sock_recv(socket_cliente, TAMANHO_MAX_DADOS)).decode(ESTILO)
            linhas = dados.split('\r\n')
            if linhas:
                linha = linhas[0]
                palavras = linha.split(' ')
                caminho = "" if len(palavras) < 2 else palavras[1]
                conteudo = await obter_pagina(caminho)
                codigo_resposta = "200 OK" if conteudo else "404 Not Found"
                # Cria a resposta
                resposta = f"HTTP/1.1 {codigo_resposta}\r\n\r\n"
                if conteudo:
                    resposta += f"{conteudo}\r\n"
                # Responde ao cliente
                await loop.sock_sendall(socket_cliente, resposta.encode(ESTILO))
        except Exception as e:
            print(str(e))
        finally:
            if socket_cliente:
                socket_cliente.close()
                print(f"Conexão encerrada de {endereco_cliente}")
    except asyncio.CancelledError:
        print("[lidar_com_requisicao] Corrotina cancelada....")


def configurar_servidor(host, porta):
    """
    Retorna um socket ouvindo em (host, porta)
    """

    # Cria um objeto socket
    # socket.AF_INET: indica IPv4
    # socket.SOCK_STREAM: indica TCP
    socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Permite reutilização do endereço local ao qual o socket está vinculado.
    # Evita o erro "Endereço já em uso" que pode ocorrer se o servidor
    # for reiniciado e o socket anterior ainda estiver no estado TIME_WAIT.
    socket_servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Vincula o socket a um host e porta específicos
    # Deve reclamar se o host ou porta não for válido
    socket_servidor.bind((host, porta))

    # socket_servidor deve ser não-bloqueante para assíncrono
    socket_servidor.setblocking(False)

    # Inicia a escuta
    socket_servidor.listen(BACKLOG)
    print(f"Servidor ouvindo em {host}:{porta}")
    return socket_servidor


async def lidar_com_conexoes(socket_servidor):
    """
    Aceita requisições HTTP (para sempre) ouvindo em
    socket_servidor
    """
    try:
        print(f"Lidando com conexão para {socket_servidor.getsockname()}, pid: {os.getpid()}, tid: {threading.get_ident()}")
        loop = asyncio.get_event_loop()
        while True:
            try:
                # Aguarda uma conexão
                # Em modo assíncrono, note que isso não vai realmente esperar, mas 'await'
                socket_cliente, endereco_cliente = await loop.sock_accept(socket_servidor) 
                print(f"Recebeu uma nova conexão de {endereco_cliente}")
                # isso cria e executa a tarefa assíncrona
                loop.create_task(lidar_com_requisicao(socket_cliente, endereco_cliente))
            except Exception as e:
                print(str(e))
    except asyncio.CancelledError:
        print("[lidar_com_conexoes] Corrotina cancelada....")
                  

def main():
    servidor_host = LOCALHOST
    servidor_porta = PORTA
    socket_servidor = None
    try:
        socket_servidor = configurar_servidor(servidor_host, servidor_porta)
    except Exception as e:
        print(str(e))
        print("configurar_servidor falhou! Saindo...")
        return
    
    if socket_servidor is None:
        print("Socket do servidor inválido. Saindo")
        return
    
    try:
        print(f"Main thread tid: {threading.get_ident()}") #identificador de thread 
        asyncio.run(lidar_com_conexoes(socket_servidor))
    except KeyboardInterrupt:
        print(f"\nSaindo devido a uma interrupção de teclado\n")
    finally:
        print("Servidor está desligando.")
        # Fecha o socket do servidor
        if socket_servidor:
            socket_servidor.close()


if __name__ == "__main__":
    main()
