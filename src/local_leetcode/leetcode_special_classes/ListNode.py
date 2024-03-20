from typing import Any, Optional


class ListNode:
    detection_str = (
        "# Definition for singly-linked list."
        "# class ListNode:"
        "#     def __init__(self, val=0, next=None):"
        "#         self.val = val"
        "#         self.next = next"
    )

    @staticmethod
    def fromList(list_in: list[Any]) -> "ListNode | None":
        dummy = curr = ListNode()
        for x in list_in:
            curr.next = ListNode(x)
            curr = curr.next
        return dummy.next

    def __init__(self, val: int = 0, next: "ListNode | None" = None):
        self.val = val
        self.next: Optional["ListNode"] = next

    def __repr__(self) -> str:
        l: list[Any] = []
        head: "ListNode | None" = self
        while head:
            l.append(head.val)
            head = head.next

        return str(l)
