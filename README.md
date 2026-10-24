# enpack

`enroyale/` は Minecraft 26.3 / Fabric Loader 0.19.5 用のクライアントパックです。Fabric API、Fabric Language Kotlin、Strata、EnPvP Client、導入 MOD の一覧を表示する Mod Menu を必須で配布します。各版とダウンロードハッシュは [pack.toml](enroyale/pack.toml) と [MOD メタデータ](enroyale/mods/) で固定します。

既存参加者は 26.3 対応インストーラを再実行してプロファイルを更新します。その後の MOD 同期は既存の unsup が起動時に行います。

EnPvP Client の版別 JAR は `artifacts/enpvp-client/<version>/` に置き、GitHub Pages から配布します。公開済みの JAR は置き換えず、変更時は新しい版のパスと SHA-256 をメタデータへ登録します。サーバー更新より先にパックを公開し、参加者の導入を確認してください。

メタデータを変更したら `enroyale/` で `packwiz refresh` を実行します。TOML はハッシュの一致を保つため LF で保存します。

```sh
python scripts/verify_pack.py --download
```

この検証はインデックスのハッシュ鎖と外部 JAR の実体を確認します。EnPvP Client は同じリポジトリ内の配布 JAR と照合するため、PR が未マージでも検証できます。Minecraft の起動確認は実際の Fabric クライアントで別途行います。
