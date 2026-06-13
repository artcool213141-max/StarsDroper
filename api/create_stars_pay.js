// api/create_stars_pay.js

export default async function handler(req, res) {
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    const { user_id, amount } = req.body;
    const BOT_TOKEN = "8877027563:AAER5zuqzfpzHZESBvj_Qd44sUkSCQT4kjI"; // Вставь сюда токен от @BotFather

    try {
        // Создаем инвойс через Telegram Bot API
        const response = await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/createInvoiceLink`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: "Пополнение баланса",
                description: `Покупка ${amount} звезд`,
                payload: `user_${user_id}_amt_${amount}`,
                currency: "XTR",
                prices: [{ label: "Звезды", amount: amount }]
            })
        });

        const data = await response.json();

        if (data.ok) {
            return res.status(200).json({ pay_url: data.result });
        } else {
            return res.status(400).json({ error: data.description });
        }
    } catch (e) {
        return res.status(500).json({ error: "Ошибка сервера" });
    }
}
