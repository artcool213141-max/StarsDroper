export default async function handler(req, res) {
    // Явно разрешаем POST
    if (req.method !== 'POST') {
        return res.status(405).json({ error: "Method not allowed, use POST" });
    }
    
    const { user_id, amount } = req.body;
    const url = `https://api.telegram.org/bot${process.env.BOT_TOKEN}/createInvoiceLink`;
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                title: "Пополнение баланса",
                description: `Пополнение на ${amount} звёзд`,
                payload: String(user_id),
                currency: "XTR",
                prices: [{ label: "Звёзды", amount: Number(amount) }]
            })
        });
        
        const data = await response.json();
        
        if (data.ok) {
            // Возвращаем именно объект, как ожидает фронтенд
            return res.status(200).json({ pay_url: data.result });
        } else {
            return res.status(400).json({ error: data.description });
        }
    } catch (e) {
        return res.status(500).json({ error: e.message });
    }
}
