class RemoteServer {
  private baseURL: URL;
  startPath: URL;

  constructor(baseURL: URL, startPath: string) {
    this.baseURL = baseURL;
    this.startPath = new URL(startPath, this.baseURL);
  }

  logsWebSocketURL(id: string): URL {
    const webSocketURL = new URL(`/ws/logs/${id}`, this.baseURL);
    webSocketURL.protocol = "ws";
    return webSocketURL;
  }

  statusWebSocketURL(id: string): URL {
    const webSocketURL = new URL(`/ws/status/${id}`, this.baseURL);
    webSocketURL.protocol = "ws";
    return webSocketURL;
  }

  statsWebSocketURL(id: string): URL {
    const webSocketURL = new URL(`/ws/stats/${id}`, this.baseURL);
    webSocketURL.protocol = "ws";
    return webSocketURL;
  }
}

type RemoteServersObject = {
  [key: string]: RemoteServer;
};

export const RemoteServers: RemoteServersObject = {
  DemoLogger: new RemoteServer(
    new URL("http://localhost:8000"),
    "/start/demo-logger",
  ),
};
