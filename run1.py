if __name__ == "__main__":
    from server.server import WordleServer
    
    server = WordleServer()
    try:
        server.start_server()
    except KeyboardInterrupt:
        print("\nServidor detenido")