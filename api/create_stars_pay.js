export default async function handler(req, res) {
    if (req.method !== 'POST') return res.status(405).send('Method not allowed');
    
    const { user_id, amount } = req.body;
    
    // Используем метод Telegram Bot API: createInvoiceLink
    // Обрати внимание: stars_amount должен быть в звездах
    const url = `https://api.telegram.org/bot${process.env.BOT_TOKEN}/createInvoiceLink`;
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                title: "Пополнение баланса",
                description: `Пополнение на ${amount} звёзд`,
                payload: String(user_id), // Сюда передаем ID юзера
                currency: "XTR", // Код валюты Telegram Stars
                prices: [{ label: "Звёзды", amount: Number(amount) }]
            })
        });
        
        const data = await response.json();
        
        if (data.ok) {
            // Возвращаем ссылку на инвойс, которую фронтенд откроет через tg.openInvoice
            return res.status(200).json({ pay_url: data.result });
        } else {
            return res.status(400).json({ error: data.description });
        }
    } catch (e) {
        return res.status(500).json({ error: e.message });
    }
}
