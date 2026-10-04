var mix = {
	methods: {
		getHistoryOrder() {
			this.getData("/api/orders")
				.then(data => {
					this.orders = data
				})
				.catch(() => {
					this.orders = []
					console.warn('Ошибка при получении списка заказов')
				})
		},
		deliveryLabel(type) {
			return { ordinary: 'Обычная', express: 'Экспресс' }[type] || type || '—'
		},
		paymentLabel(type) {
			return { online: 'Онлайн картой', someone: 'Со чужого счёта' }[type] || type || '—'
		},
		statusLabel(status) {
			return {
				new: 'Новый',
				accepted: 'Принят',
				paid: 'Оплачен',
				failed: 'Ошибка оплаты'
			}[status] || status || '—'
		}
	},
	mounted() {
		this.getHistoryOrder()
	},
	data() {
		return {
			orders: [],
		}
	},
}
