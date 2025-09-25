from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass
class DHParams:
    # DH public parameters: prime p and generator g for (Z/pZ)*.
    p: int
    g: int

DH_PARAMS = DHParams(p=23, g=5)


@dataclass
class ClientHello:
    requested_group: str = "DH_23_5"


@dataclass
class ServerHello:
    selected_group: str
    params: DHParams


@dataclass
class ClientKeyShare:
    # Client public: A = g^a mod p
    A: int


@dataclass
class ServerKeyShare:
    # Server public: B = g^b mod p
    B: int


@dataclass
class Finished:
    ok: bool  # handshake success flag


def dh_public(g: int, a: int, p: int) -> int:
    """
    Public value:
        A = g^a mod p   or   B = g^b mod p
    """
    return pow(g, a, p)


def dh_shared(pub_other: int, a: int, p: int) -> int:
    """
    Shared secret from holder of exponent a:
        K = (pub_other)^a mod p
          = (g^b)^a = g^{ba}  (client)
          = (g^a)^b = g^{ab}  (server)
    """
    return pow(pub_other, a, p)


class DHClient:

    def __init__(self, params: DHParams):
        self.params = params
        self.a: Optional[int] = None  # private
        self.A: Optional[int] = None  # public
        self.shared: Optional[int] = None

    def start(self) -> ClientHello:
        print("[Client] -> ClientHello(requested_group=DH_23_5)")
        return ClientHello()

    def on_server_hello(self, sh: ServerHello) -> ClientKeyShare:
        assert sh.params == self.params
        print(f"[Client] <- ServerHello(selected_group={sh.selected_group}, p={sh.params.p}, g={sh.params.g})")

        self.a = 6

        # A = g^a mod p
        self.A = dh_public(self.params.g, self.a, self.params.p)
        print(f"[Client]   a={self.a}, A = g^a mod p = {self.A}")

        print("[Client] -> ClientKeyShare(A)")
        return ClientKeyShare(A=self.A)

    def on_server_keyshare(self, sk: ServerKeyShare) -> Finished:
        # K_client = B^a mod p
        assert self.a is not None
        self.shared = dh_shared(sk.B, self.a, self.params.p)
        print(f"[Client] <- ServerKeyShare(B={sk.B})")
        print(f"[Client]   shared = B^a mod p = {self.shared}")

        print("[Client] -> Finished")
        return Finished(ok=True)


class DHServer:

    def __init__(self, params: DHParams):
        self.params = params
        self.b: Optional[int] = None  # private
        self.B: Optional[int] = None  # public
        self.shared: Optional[int] = None

    def on_client_hello(self, ch: ClientHello) -> ServerHello:
        print("[Server] <- ClientHello")
        print("[Server] -> ServerHello(selected_group=DH_23_5, params)")
        return ServerHello(selected_group="DH_23_5", params=self.params)

    def on_client_keyshare(self, ck: ClientKeyShare) -> Tuple[ServerKeyShare, Finished]:
        print(f"[Server] <- ClientKeyShare(A={ck.A})")

        self.b = 15

        # B = g^b mod p
        self.B = dh_public(self.params.g, self.b, self.params.p)
        print(f"[Server]   b={self.b}, B = g^b mod p = {self.B}")

        # K_server = A^b mod p
        self.shared = dh_shared(ck.A, self.b, self.params.p)
        print(f"[Server]   shared = A^b mod p = {self.shared}")

        print("[Server] -> ServerKeyShare(B)")
        print("[Server] -> Finished")
        return ServerKeyShare(B=self.B), Finished(ok=True)


def main() -> None:
    params = DH_PARAMS
    client = DHClient(params)
    server = DHServer(params)

    # 1) ClientHello
    ch = client.start()

    # 2) ServerHello
    sh = server.on_client_hello(ch)
    ck = client.on_server_hello(sh)

    # 3) KeyShare exchange + Finished
    sk, fin_srv = server.on_client_keyshare(ck)
    fin_cli = client.on_server_keyshare(sk)

    print("\n=== Handshake Result ===")
    print(f"Client shared: {client.shared}")
    print(f"Server shared: {server.shared}")
    print(f"Equal? {client.shared == server.shared}")
    print(f"Finished(C): {fin_cli.ok}, Finished(S): {fin_srv.ok}")


if __name__ == "__main__":
    main()
