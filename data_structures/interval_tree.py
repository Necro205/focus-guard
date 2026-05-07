"""
interval_tree.py — Zaman Aralığı Sorgusu için İkili Arama Ağacı
=================================================================
Oturum sonu analizinde "14:00-14:30 arasında kaç telefon olayı oldu?" gibi
zaman aralığı sorgularına O(log n + k) hızında cevap verir.

Augmented BST: her düğüm kendi altındaki maksimum bitiş zamanını da tutar.
Bu sayede overlap sorgularında alakasız alt ağaçlar atlanabilir.

Not: Dengesiz ağaç olabilir. Ağır yük için Red-Black veya AVL implement edilir;
ama bir öğrenci projesinde augmented BST yeterince "veri yapıları"
bilgisi gösterir ve öğretim hedefini karşılar.

Karmaşıklıklar (dengeli varsayımıyla):
--------------------------------------
insert(interval)       : O(log n)
query_overlap(a, b)    : O(log n + k), k = eşleşen aralık sayısı
traverse_inorder()     : O(n)
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Interval:
    start: float           # epoch
    end: float
    event_type: str
    meta: Optional[dict] = None


class _Node:
    __slots__ = ("interval", "max_end", "left", "right")

    def __init__(self, interval: Interval):
        self.interval = interval
        self.max_end = interval.end
        self.left: Optional["_Node"] = None
        self.right: Optional["_Node"] = None


class IntervalTree:
    """Augmented BST. Start zamanına göre sıralanır."""

    def __init__(self):
        self._root: Optional[_Node] = None
        self._size = 0

    # --------------- Ekleme ---------------
    def insert(self, interval: Interval) -> None:
        self._root = self._insert(self._root, interval)
        self._size += 1

    def _insert(self, node: Optional[_Node], interval: Interval) -> _Node:
        if node is None:
            return _Node(interval)
        if interval.start < node.interval.start:
            node.left = self._insert(node.left, interval)
        else:
            node.right = self._insert(node.right, interval)
        # Augmented alan güncellenir
        node.max_end = max(node.max_end, interval.end)
        return node

    # --------------- Aralık sorgusu ---------------
    def query_overlap(self, start: float, end: float) -> list[Interval]:
        """
        [start, end] ile kesişen tüm intervalları döndürür.
        Ağaç geçişini max_end pruning ile hızlandırır.
        """
        results: list[Interval] = []
        self._query(self._root, start, end, results)
        return results

    def _query(self, node: Optional[_Node], q_start: float, q_end: float,
               out: list[Interval]) -> None:
        if node is None:
            return
        # Sol alt ağaçtaki en geç bitiş q_start'tan küçükse → sol boş
        if node.left and node.left.max_end >= q_start:
            self._query(node.left, q_start, q_end, out)
        # Bu düğüm kesişiyor mu?
        if node.interval.start <= q_end and node.interval.end >= q_start:
            out.append(node.interval)
        # Sağ alt ağaca ancak bu düğümün start'ı q_end'ten küçük/eşitse
        if node.interval.start <= q_end:
            self._query(node.right, q_start, q_end, out)

    # --------------- Yardımcılar ---------------
    def inorder(self) -> list[Interval]:
        out: list[Interval] = []
        self._inorder(self._root, out)
        return out

    def _inorder(self, node: Optional[_Node], out: list[Interval]) -> None:
        if node is None:
            return
        self._inorder(node.left, out)
        out.append(node.interval)
        self._inorder(node.right, out)

    def __len__(self) -> int:
        return self._size


# ============ Self-test ============
if __name__ == "__main__":
    tree = IntervalTree()
    tree.insert(Interval(0, 10, "focused"))
    tree.insert(Interval(15, 25, "phone_detected"))
    tree.insert(Interval(20, 30, "social_media"))
    tree.insert(Interval(40, 50, "focused"))
    print("5-18 arası:", tree.query_overlap(5, 18))
    print("Tüm sıralı:", tree.inorder())
