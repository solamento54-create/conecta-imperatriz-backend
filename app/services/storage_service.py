class SupabaseStorage(StorageBackend):
    """Storage que salva arquivos no Supabase Storage via REST API."""

    def __init__(self):
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise ValueError(
                "STORAGE_MODE=supabase requer SUPABASE_URL e SUPABASE_KEY no .env"
            )
        self.url = settings.SUPABASE_URL.rstrip("/")
        self.key = settings.SUPABASE_KEY
        self.bucket = settings.SUPABASE_BUCKET
        self.headers = {
            "Authorization": f"Bearer {self.key}",
            "apikey": self.key,
        }
        self._garantir_bucket()

    def _garantir_bucket(self):
        try:
            import requests
            r = requests.get(
                f"{self.url}/storage/v1/bucket/{self.bucket}",
                headers=self.headers,
                timeout=10
            )
            if r.status_code == 404:
                requests.post(
                    f"{self.url}/storage/v1/bucket",
                    headers={**self.headers, "Content-Type": "application/json"},
                    json={"id": self.bucket, "name": self.bucket, "public": True},
                    timeout=10
                )
        except Exception as e:
            print(f"⚠️  Aviso bucket: {e}")

    def upload(self, conteudo: bytes, caminho: str, content_type: str = "image/jpeg") -> str:
        import requests
        r = requests.post(
            f"{self.url}/storage/v1/object/{self.bucket}/{caminho}",
            headers={
                **self.headers,
                "Content-Type": content_type,
                "x-upsert": "true",
            },
            data=conteudo,
            timeout=30
        )
        if r.status_code not in (200, 201):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Falha no upload: {r.text}"
            )
        return self.url_publica(caminho)

    def delete(self, caminho: str) -> bool:
        import requests
        try:
            requests.delete(
                f"{self.url}/storage/v1/object/{self.bucket}/{caminho}",
                headers=self.headers,
                timeout=10
            )
            return True
        except Exception:
            return False

    def url_publica(self, caminho: str) -> str:
        return f"{self.url}/storage/v1/object/public/{self.bucket}/{caminho}"
