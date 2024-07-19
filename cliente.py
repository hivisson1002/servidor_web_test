"""
Um script genérico para enviar qualquer solicitação a qualquer host e porta.

./send_to_server <host> <port> <"request">
"""
import argparse
import socket

# Tamanho máximo dos dados lidos de um socket
TAMANHO_MAX_DADOS = 1024

# Estilo de codificação
ESTILO = "utf-8"

def tratar_solicitacao(args):
    """
    Envia a solicitação para o servidor que está ouvindo em host e porta,
    e imprime caso haja uma resposta do servidor.
    
    Args:
        args (Namespace): Argumentos contendo host, port e request.
    """
    cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        cliente_socket.connect((args.host, int(args.port)))  # Conecta ao servidor especificado
        cliente_socket.sendall(args.request.encode(ESTILO))  # Envia a solicitação codificada
        dados = cliente_socket.recv(TAMANHO_MAX_DADOS)  # Recebe a resposta do servidor
        if dados:
            print(dados.decode(ESTILO))  # Imprime a resposta decodificada
    except ConnectionRefusedError:
        print(f"Conexão recusada. O servidor pode estar fora do ar ou a porta {args.port} está incorreta.")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")
    finally:
        cliente_socket.close()  # Fecha o socket

def main():
    """
    Função principal que parseia os argumentos e chama a função para tratar a solicitação.
    """
    parser = argparse.ArgumentParser(description="Um script cliente para se comunicar com um servidor genérico")
    
    parser.add_argument("host")  # Argumento para o endereço do host
    parser.add_argument("port")  # Argumento para a porta do servidor
    parser.add_argument("request")  # Solicitação a ser enviada, deve estar entre aspas
    args = parser.parse_args()

    tratar_solicitacao(args)

if __name__ == '__main__':
    main()

