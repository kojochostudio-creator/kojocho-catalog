# KOJOCHO_CATALOG_CURRENT_PRODUCT_SYNC_V01

確認日: 2026-09-22 JST。既存checkoutのoriginは `https://github.com/kojochostudio-creator/kojocho-catalog.git`。

確定差分のローカル同期・生成・表示検証は完了。販売先の全件リンク検証は未完了のため、公開READYとは判定しない。

```text
BEFORE_PRODUCT_COUNT=20
AFTER_PRODUCT_COUNT=120
ADDED=100
UPDATED=20
REMOVED_OR_HIDDEN=0
UNCHANGED=0
CATALOG_EXISTING_PRODUCT_COUNT=20
CURRENT_SELLABLE_PRODUCT_COUNT=120
MISSING_IN_CATALOG=100 -> 0 (確認済み120商品内)
STALE_IN_CATALOG=0 (確認済み既存20商品内)
URL_MISMATCH_COUNT=0 (確定した既存商品の差分)
PRICE_MISMATCH_COUNT=1 -> 0 (既存商品のitch.io価格)
BROKEN_LINK_COUNT=0 (実測で確認された切れのみ。未確認を含めた全件ゼロではない)
LOCAL_BROKEN_LINK_COUNT=0
DUPLICATE_PRODUCT_COUNT=0
UNKNOWN_COUNT=6
BOOTH_LINKS_VALID=UNRESOLVED
ITCH_LINKS_VALID=UNRESOLVED
CATALOG_BUILD=PASS
LOCAL_RENDER=PASS
PUBLIC_PUSH_STATUS=BLOCKED_UNRESOLVED_LINK_VALIDATION
NEXT_STEP=VERIFY_UNRESOLVED_MARKETPLACE_STATE_AND_LINKS
STATUS=STOPPED_WITH_REASON
```

120は現在のitch.io公開一覧と一致する親商品数。BOOTHの独立した無料sampler 1販売面とitch.ioの無料demo 2面は、対応する親商品のリンクとして掲載し二重計上しない。BOOTHのみの商品全体は今回列挙できておらず、全販売先を合わせた総数が120とは断定しない。

## 反映内容

- 台帳103商品すべてを公開itch.io一覧のURLと一致照合。台帳外の公開17商品も追加し、全120商品に `status=PUBLISHED` とfamilyを付与。台帳の検品状態だけで公開可否を決めていない。
- 既存20件のURL・タイトル・coverは維持。ID 93「Japanese Woodworking Workshop Props - 12 PNG Set」のitch.io価格だけを、公開表示に基づき `1 USD` から `2 USD` へ修正。UPDATED=20にはstatus/family追加を含み、価格以外の既存商品情報19件はそのまま。
- family内訳: Icon 25、Pixel Art 6、3D 5、PNG / Scene Props 71、Bundles 12、Tools 1。既存分類IDを維持し、Start Here、Free / Sampler、3D、PNG / Scene Props、Toolsの所属を追加。Tools 1件は公開Unity郵便番号ツールを誤分類しないための補助分類。
- New Releasesの所属6件を取得時の公開ショップ先頭6商品へ更新。メイン・サブの特集商品は維持。
- 無料ポーション素材、SKY ATELIERの無料demo/BOOTH sampler、薬屋アイコンの無料demoへ実在の導線を追加。demoは実ページの `#demo` を確認。有料商品そのものを無料として表示していない。
- 3Dは看板、鳥居、襖、湯呑み、和室・旅館10GLBの5商品。WIP、公開未確認の制作候補、凍結中の学校体育館素材は追加していない。
- 和室・旅館10GLB: `FAB_STATUS=FAB_PLANNED`（ユーザー指定の初回候補）。Fab公開・URLは未確認。公開CatalogにFabリンクを追加していない。
- 販売先片側のみ・価格空欄の表示とsampler導線のため、既存JSを最小変更。分類数7の固定チェックを、既存7分類の必須存在・全分類IDの非空/重複なしチェックに変更。

## 未確定部分

`UNKNOWN_COUNT=6` は販売先URLまたは価格の値が未確定の「商品数」。日本語の正式タイトルを全文確認できていない17件は翻訳や省略表示からの復元で補わず空欄とし、この販売先カウントには含めない。

- BOOTH URL未確定5商品: Unity郵便番号ツール、江戸木看板Vol.1/Vol.2、3D鳥居、薬屋調合アイコン。確認できたitch.io側は掲載し、BOOTHリンクは空欄。
- 無料ポーション素材: BOOTH URLは現行itch.io本文のリンクから確認したが、BOOTH価格は未確定。`See store` と表示し、itch.io側の無料価格を転用していない。
- 薬屋のローカル出品準備資料は公開証拠とは扱わない。旧準備価格$1.99ではなく、現行公開ページの$2.99を採用。準備記録だけのsampler BOOTH URLは追加していない。
- 学校教室のBOOTH URLは出版台帳に記載された `ko-jo-cho-studio.booth.pm/items/8852176` を保存。和室・旅館は公開記録に実測resolved URLとして記載された `https://booth.pm/ja/items/8814332` を採用。異なるshop hostnameがあるため、現行BOOTHでの解決確認が必要。
- BOOTHは既存shop URL、出版記録のshop URL、出版記録の正規item URLの読み取りがHTTP 403。商品リンク115件＋samplerリンク1件の現時点有効性・価格、およびBOOTH専売品の網羅性は未確定。403を商品削除・リンク切れとは判定していない。既存/出版記録由来のBOOTH価格を現在再検証済みとは扱わない。
- itch.io公開プロフィールはHTTP 200で120件を取得。個別ページは85件がHTTP 200、35件がHTTP 429。このバッチの結果確認後は追加取得・再試行を行っていない。未確認35件をリンク切れまたはPASSとは判定していない。

## 変更ファイルと検証

公開側の変更は `products.json`、`site_taxonomy.json`、`site_config.json`、`assets/js/catalog.js`、`assets/js/collection-page.js`、追加cover 100件、本レポート。coverは公開ページに指定されたPNGをそのままコピーし、商品Artは加工していない。既存collection/detail生成器を実行したが、HTML内容に差分はない。

- 構文検査、データ照合、cover 120件のdecode、重複/分類参照/ローカルリンク検証: PASS。
- 同じ入力から再生成してproducts/taxonomy/config/既存11 HTMLのSHA-256が一致: PASS。
- Playwright実ブラウザ: 120カード展開、販売先/samplerリンク、3D/Free・Sampler/Pixel Artの所属、4 collectionページ、5 detailページ、幅390pxでの横overflowなし: PASS。外部通信を遮断してローカルのみで実施。
- 既存CSS、トップHTML、FAQ、canonical、sitemap、robots、analytics設定: 維持。台帳DBの前後SHA-256一致: PASS。
- BOOTH/itch.ioの商品編集、ZIP変更、Product Factory変更、git commit/push: 未実施。
- 作業開始時から未追跡だった `site_product_pages_v01.json` は既存内容を維持。

再現用の同期/検証スクリプトと取得証拠は既存gitignore対象の `tools/` 内。旧台帳のみを前提にする `REFRESH_CATALOG.bat` では今回の台帳外17商品を再生成できないため、この同期の再現には `python -B tools/sync_current_products_v01.py`、`python -B tools/test_catalog_sync_data_v01.py` を使用する。

根拠: [現行itch.ioショップ](https://kojochostudio.itch.io/)、`D:\商品台帳_SQLite\product_ledger.db`（read-only）、3D Factory `CURRENT_STATE.md` / `ryokan_publication_record_v01.json`、Pixel Art Factory `docs/PUBLISH_LEDGER_V01.md`、Icon FactoryのSKY ATELIER・侍アイコン公開closeout。取得原本・個別リンク結果・差分基準・表示画像は `tools/sync_evidence_v01/`。

次の作業は、未確認の販売先状態・リンクを通常の閲覧環境で確認すること。その確認を完了してからREADY判定する。今回pushはしない。
