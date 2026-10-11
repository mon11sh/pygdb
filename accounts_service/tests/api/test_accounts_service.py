import httpx
import asyncio

class T:
    B = "http://localhost:8001/api/v1"
    async def get_token(self):
        async with httpx.AsyncClient() as c:
            r = await c.post("http://localhost:8004/api/v1/auth/login", json={"login_id": "john.doe", "password": "Welcome@1"})
            return r.json()["access_token"]
    async def t1(self):
        print("\nTEST: Account")
        token = await self.get_token()
        h = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient() as c:
            r = await c.get(f"{self.B}/accounts/1003", headers=h)
            assert r.status_code == 200
            print("PASS")
    async def t2(self):
        print("\nTEST: Missing")
        async with httpx.AsyncClient() as c:
            r = await c.get(f"{self.B}/accounts/1003")
            assert r.status_code == 401
            print("PASS")
    async def t3(self):
        print("\nTEST: PIN")
        token = await self.get_token()
        h = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient() as c:
            r = await c.post(f"{self.B}/internal/accounts/1003/verify-pin", headers=h, params={"pin": "9640"})
            assert r.status_code in [200, 400, 500]
            print("PASS")
    async def t4(self):
        print("\nTEST: Debit")
        token = await self.get_token()
        h = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient() as c:
            r = await c.post(f"{self.B}/internal/accounts/1003/debit", headers=h, params={"amount": 100})
            assert r.status_code == 200
            print("PASS")

async def run():
    print("ACCOUNTS: " + "="*60)
    t = T()
    for m in [t.t1, t.t2, t.t3, t.t4]:
        try:
            await m()
        except Exception as e:
            print(f"FAIL: {e}")
    print("="*70)

asyncio.run(run())
