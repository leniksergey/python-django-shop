var mix = {
	methods: {
		validatePayment() {
			const errs = {}

			const name = (this.name || '').trim()
			if (!name) {
				errs.name = 'Укажите имя владельца карты'
			} else if (name.length < 2) {
				errs.name = 'Имя слишком короткое'
			} else if (!/^[A-Za-zА-Яа-яЁё\s.\-]+$/.test(name)) {
				errs.name = 'Только буквы, пробел, точка и дефис'
			}

			const number = (this.number1 || '').replace(/\D/g, '')
			if (!number) {
				errs.number1 = 'Укажите номер карты'
			} else if (number.length < 13 || number.length > 19) {
				errs.number1 = 'Номер должен содержать 13–19 цифр'
			} else if (!this.luhnCheck(number)) {
				errs.number1 = 'Некорректный номер карты'
			}

			const month = parseInt(this.month, 10)
			if (!this.month && this.month !== 0) {
				errs.month = 'Укажите месяц'
			} else if (isNaN(month) || month < 1 || month > 12) {
				errs.month = 'Месяц от 1 до 12'
			}

			const year = parseInt(this.year, 10)
			const currentYear = new Date().getFullYear()
			const currentMonth = new Date().getMonth() + 1
			if (!this.year && this.year !== 0) {
				errs.year = 'Укажите год'
			} else if (isNaN(year) || year < currentYear) {
				errs.year = 'Год не может быть меньше текущего'
			} else if (year > currentYear + 15) {
				errs.year = 'Слишком далёкий год'
			} else if (month && year === currentYear && month < currentMonth) {
				errs.year = 'Срок действия карты истёк'
			}

			const code = (this.code || '').trim()
			if (!code) {
				errs.code = 'Укажите CVV'
			} else if (!/^\d{3}$/.test(code)) {
				errs.code = 'CVV — ровно 3 цифры'
			}

			this.errors = errs
			return Object.keys(errs).length === 0
		},

		luhnCheck(number) {
			const digits = number.split('').map(Number)
			let sum = 0
			const parity = digits.length % 2
			for (let i = 0; i < digits.length; i++) {
				let d = digits[i]
				if (i % 2 === parity) {
					d *= 2
					if (d > 9) d -= 9
				}
				sum += d
			}
			return sum % 10 === 0
		},

		submitPayment() {
			if (!this.validatePayment()) {
				return
			}
			const orderId = location.pathname.startsWith('/payment/')
				? Number(location.pathname.replace('/payment/', '').replace('/', ''))
				: null

			this.postData(`/api/payment/${orderId}`, {
				name: this.name,
				number: this.number1,
				year: this.year,
				month: this.month,
				code: this.code,
			})
				.then(() => {
					alert('Успешная оплата')
					this.number1 = ''
					this.name = ''
					this.year = ''
					this.month = ''
					this.code = ''
					this.errors = {}
					location.assign('/')
				})
				.catch((err) => {
					const errors = err?.response?.data?.errors
					if (errors) {
						this.errors = errors
					} else {
						alert('Ошибка при оплате')
					}
				})
		},
	},

	watch: {
		name() { this.validatePayment() },
		number1() { this.validatePayment() },
		month() { this.validatePayment() },
		year() { this.validatePayment() },
		code() { this.validatePayment() },
	},

	data() {
		return {
			number1: '',
			month: '',
			year: '',
			name: '',
			code: '',
			errors: {},
		}
	},
}
