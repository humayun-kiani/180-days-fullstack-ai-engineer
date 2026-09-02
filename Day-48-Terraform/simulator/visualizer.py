# simulator/visualizer.py
# Pretty-print plan and apply results

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    class Fore:
        GREEN = YELLOW = RED = CYAN = WHITE = BLUE = ""
    class Style:
        RESET_ALL = BRIGHT = ""
    HAS_COLOR = False


def print_banner():
    print(f"\n{'═' * 65}")
    print(f"  {Fore.CYAN}Infrastructure as Code with Terraform{Style.RESET_ALL}")
    print(f"  Day 48 — Task API Infrastructure Simulator")
    print(f"{'═' * 65}\n")


def print_plan(plan: dict, environment: str):
    """Pretty-print a terraform plan."""
    s = plan["summary"]
    total_changes = s["create"] + s["update"] + s["destroy"]

    print(f"{Fore.CYAN}Terraform Plan — {environment}{Style.RESET_ALL}")
    print(f"{'─' * 50}")

    if total_changes == 0:
        print(f"  {Fore.GREEN}✅ No changes. Infrastructure is up-to-date.{Style.RESET_ALL}")
        return

    if plan["to_create"]:
        print(f"\n  {Fore.GREEN}Resources to CREATE (+{s['create']}):{Style.RESET_ALL}")
        for item in plan["to_create"]:
            print(f"    {Fore.GREEN}+{Style.RESET_ALL} {item['type']}.{item['key'].split('.')[1]}")

    if plan["to_update"]:
        print(f"\n  {Fore.YELLOW}Resources to UPDATE (~{s['update']}):{Style.RESET_ALL}")
        for item in plan["to_update"]:
            key = item['key']
            print(f"    {Fore.YELLOW}~{Style.RESET_ALL} {key}")
            for field, diff in item["changes"].items():
                print(f"      {field}: {Fore.RED}{diff['old']}{Style.RESET_ALL} → "
                      f"{Fore.GREEN}{diff['new']}{Style.RESET_ALL}")

    if plan["to_destroy"]:
        print(f"\n  {Fore.RED}Resources to DESTROY (-{s['destroy']}):{Style.RESET_ALL}")
        for item in plan["to_destroy"]:
            print(f"    {Fore.RED}-{Style.RESET_ALL} {item['key']} ({item['real_id']})")

    print(f"\n  {Fore.CYAN}Plan:{Style.RESET_ALL} "
          f"{Fore.GREEN}+{s['create']}{Style.RESET_ALL} "
          f"{Fore.YELLOW}~{s['update']}{Style.RESET_ALL} "
          f"{Fore.RED}-{s['destroy']}{Style.RESET_ALL}")


def print_apply(results: dict):
    """Pretty-print apply results."""
    total = (len(results.get("created", [])) +
             len(results.get("updated", [])) +
             len(results.get("destroyed", [])))

    if "message" in results:
        print(f"\n  {Fore.GREEN}✅ {results['message']}{Style.RESET_ALL}")
        return

    print(f"\n  {Fore.GREEN}Apply complete! {total} change(s).{Style.RESET_ALL}\n")

    for r in results.get("created", []):
        print(f"    {Fore.GREEN}✅ Created:{Style.RESET_ALL} {r['key']} → {r['real_id']}")

    for r in results.get("updated", []):
        print(f"    {Fore.YELLOW}✏️  Updated:{Style.RESET_ALL} {r['key']} "
              f"(changed: {', '.join(r['changes'])})")

    for r in results.get("destroyed", []):
        print(f"    {Fore.RED}🗑️  Destroyed:{Style.RESET_ALL} {r['key']}")


def print_state(state: dict):
    """Show current state in a readable format."""
    resources = state["resources"]
    print(f"\n  {Fore.CYAN}Current State ({state['total']} resources):{Style.RESET_ALL}")
    print(f"  {'─' * 50}")

    by_type = {}
    for key, r in resources.items():
        t = r["type"]
        if t not in by_type:
            by_type[t] = []
        by_type[t].append(r)

    for rtype, items in sorted(by_type.items()):
        print(f"\n  {Fore.BLUE}{rtype}{Style.RESET_ALL} ({len(items)})")
        for r in items:
            print(f"    • {r['name']} → {r['id']}")

    print()