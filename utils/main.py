def fmt_accounts(rows: list[dict]) -> str:
    txt = ["<b>💰 Ваши счета:</b>"]
    for r in rows:
        txt.append(f"#{r['account_id']} <b>{r['name']}</b> [{r['currency']}] — {r['current_balance']:.2f}")
    return "\n".join(txt)

def fmt_transactions(rows: list[dict]) -> str:
    txt = ["<b>📋 Транзакции:</b>"]
    for r in rows:
        sign = "➕" if r['type']=="I" else "➖"
        date = r['occurred_at'].strftime("%Y-%m-%d")
        line = f"#{r['transaction_id']} {date} {sign} <b>{r['amount']:.2f}</b> • {r['account']}/{r['category']}"
        if r['description']:
            line += f"\n    «{r['description']}»"
        if r['tags']:
            line += f" 🏷️ {r['tags']}"
        txt.append(line)
    return "\n".join(txt)

def fmt_budgets(rows: list[dict]) -> str:
    txt = ["<b>📊 Бюджеты:</b>"]
    for r in rows:
        rem = float(r['amount_limit']) - float(r['spent'])
        pct = float(r['spent'])/float(r['amount_limit'])*100 if r['amount_limit']>0 else 0
        txt.append(
            f"#{r['budget_id']} <b>{r['category']}</b> {r['start_date']}—{r['end_date']}\n"
            f"    Лимит: {r['amount_limit']:.2f}  Потрачено: {r['spent']:.2f}  Осталось: {rem:.2f} ({pct:.0f}%)"
        )
    return "\n".join(txt)

def fmt_goals(rows: list[dict]) -> str:
    txt = ["<b>🎯 Цели:</b>"]
    for r in rows:
        pct = float(r['saved_amount'])/float(r['target_amount'])*100 if r['target_amount']>0 else 0
        status = "✔️" if r['is_achieved'] else ("⚠️" if pct>=90 else "🔄")
        txt.append(
            f"#{r['goal_id']} <b>{r['name']}</b> {r['saved_amount']:.2f}/{r['target_amount']:.2f} ({pct:.0f}%)\n"
            f"    Дедлайн: {r['due_date']} {status}"
        )
    return "\n".join(txt)

def fmt_recurring(rows: list[dict]) -> str:
    txt = ["<b>⏱️ Повторяющиеся:</b>"]
    for r in rows:
        txt.append(
            f"#{r['recur_id']} acc={r['account_id']} cat={r['category_id']} amt={r['amount']:.2f} {r['type']}\n"
            f"    next: {r['next_run']} every {r['freq_interval']}\n"
            f"    «{(r['description'] or '')}»"
        )
    return "\n".join(txt)