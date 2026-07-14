# Day 07 — Object Oriented Programming (OOP) + Week 1 Revision

> **Phase 1 — Foundations** | Week 1 | Day 7 of 180

---

## 📌 What I Learned Today

- What OOP is and why it exists
- Classes — the blueprint for objects
- Objects — instances created from a class
- The **init** method — the constructor
- The self keyword — how objects reference themselves
- Instance variables vs class variables
- Encapsulation — protecting data with private attributes
- The @property decorator — clean attribute access control
- Inheritance — building child classes from parent classes
- super() — calling parent class methods from child class
- Polymorphism — same method name, different behavior
- Method overriding — redefining parent methods in child class
- Dunder methods: **str**, **repr**, **len**, **eq**, **lt**, **add**
- @classmethod and @staticmethod decorators
- Multi-level inheritance — PremiumAccount extends SavingsAccount extends BankAccount
- Custom exceptions for domain-specific errors

## 🔨 Project Built

**Complete Bank Account System** — Full OOP implementation:

- BankAccount base class with deposit, withdraw, transfer, statement
- SavingsAccount — 6% interest, monthly withdrawal limits, minimum balance
- CheckingAccount — overdraft protection up to Rs.25,000
- PremiumAccount — 8% interest + 2% cashback + reward points
- BankSystem manager class — creates, stores, retrieves accounts
- All accounts auto-saved to bank_data.json
- Data persists between sessions
- All dunder methods implemented
- Custom exceptions: InsufficientFundsError, InvalidAmountError, AccountNotFoundError
- Full menu-driven interface with 7 operations

## 🚀 How to Run

```bash
cd Day-07-OOP-and-Classes
python main.py
```

## 🧠 OOP Hierarchy

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
