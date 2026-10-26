from collections import defaultdict
from qgis.core import (
    QgsVectorLayer, QgsGeometry, QgsFeature, QgsField,
    QgsProject, QgsDistanceArea,
)
from qgis.PyQt.QtCore import QVariant


def merge_regions():
    src = iface.activeLayer()
    required = {"巣箱数", "営巣数", "ビーフォレスト名"}

    if not isinstance(src, QgsVectorLayer):
        raise ValueError("対象のポリゴンレイヤーを選択してください")
    if not required.issubset(src.fields().names()):
        raise ValueError(f"必要なフィールドがありません: {required}")
    if not src.crs().isValid():
        raise ValueError("入力レイヤーの座標系が未設定です")

    features = sorted(src.getFeatures(), key=lambda f: f.id())
    if not features:
        raise ValueError("入力レイヤーが空です")

    geoms = [f.geometry() for f in features]
    boxes = [int(str(f["巣箱数"]).strip()) for f in features]
    nests = [int(str(f["営巣数"]).strip()) for f in features]

    for i, geom in enumerate(geoms):
        if geom.isNull() or geom.isEmpty() or not geom.isGeosValid():
            raise ValueError(f"不正または空の図形: fid={features[i].id()}")
        if not 0 <= nests[i] <= boxes[i]:
            raise ValueError(f"個数が不正: fid={features[i].id()}")

    # 重なりを調べ、連鎖してつながる地点を同じグループにする
    parent = list(range(len(features)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(features)):
        for j in range(i):
            if not geoms[i].boundingBox().intersects(geoms[j].boundingBox()):
                continue
            overlap = geoms[i].intersection(geoms[j])
            if overlap.lastError():
                raise ValueError(f"交差処理に失敗: {i}, {j}")
            if overlap.area() > 0:
                parent[root(i)] = root(j)

    groups = defaultdict(list)
    for i in range(len(features)):
        groups[root(i)].append(i)

    # 面積は WGS84 楕円体に基づく m² で計算
    measure = QgsDistanceArea()
    measure.setSourceCrs(src.crs(), QgsProject.instance().transformContext())
    if not measure.setEllipsoid("WGS84"):
        raise ValueError("面積計算の設定に失敗しました")

    out = QgsVectorLayer(
        "MultiPolygon", src.name() + "_統合結果", "memory"
    )
    out.setCrs(src.crs())
    provider = out.dataProvider()
    provider.addAttributes([
        QgsField("region_id", QVariant.Int),
        QgsField("巣箱数", QVariant.Int),
        QgsField("営巣数", QVariant.Int),
        QgsField("営巣率", QVariant.Double),
        QgsField("面積", QVariant.Double),
        QgsField("ビーフォレスト名一覧", QVariant.String),
        QgsField("元地点数", QVariant.Int),
    ])
    out.updateFields()

    rows = []
    for region_id, members in enumerate(groups.values(), start=1):
        merged = QgsGeometry.unaryUnion([geoms[i] for i in members])
        if merged.isNull() or merged.isEmpty() or not merged.isGeosValid():
            raise ValueError(f"図形の統合に失敗: region_id={region_id}")
        merged.convertToMultiType()

        total_boxes = sum(boxes[i] for i in members)
        total_nests = sum(nests[i] for i in members)
        names = list(dict.fromkeys(
            str(features[i]["ビーフォレスト名"]) for i in members
        ))

        row = QgsFeature(out.fields())
        row.setGeometry(merged)
        row.setAttributes([
            region_id,
            total_boxes,
            total_nests,
            total_nests / total_boxes if total_boxes else None,
            measure.measureArea(merged),
            ", ".join(names),
            len(members),
        ])
        rows.append(row)

    ok, _ = provider.addFeatures(rows)
    if not ok:
        raise RuntimeError("結果レイヤーへの書き込みに失敗しました")

    actual = list(out.getFeatures())
    if (
        sum(f["巣箱数"] for f in actual) != sum(boxes)
        or sum(f["営巣数"] for f in actual) != sum(nests)
        or sum(f["元地点数"] for f in actual) != len(features)
    ):
        raise RuntimeError("統合前後で合計が一致しません")

    out.updateExtents()
    QgsProject.instance().addMapLayer(out)
    print(f"地点数: {len(features)} → {out.featureCount()}")
    print(f"巣箱数: {sum(boxes)} / 営巣数: {sum(nests)}")
    print("統合前後の合計一致を確認しました。結果は一時レイヤーです。")


merge_regions()
