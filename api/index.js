const { Bot } = require('grammy');
const bot = new Bot(process.env.BOT_TOKEN); // Токен бота должен быть в переменных окружения Vercel

export default async function handler(req, res) {
    if (req.method !== 'POST') {
        return res.status(405).json({ error: "Только POST запросы" });
    }

    const { amount } = req.body;

    try {
        // Создаем ссылку для оплаты через Stars
        const link = await bot.api.createInvoiceLink(
            "Пополнение баланса",
            "Покупка звезд в NowearSpin",
            "payload_data",
            "", 
            "XTR", 
            [{ label: "Stars", amount: amount }]
        );

        return res.status(200).json({ pay_url: link });
    } catch (error) {
        console.error(error);
        return res.status(500).json({ error: "Ошибка при создании платежа" });
    }
}
