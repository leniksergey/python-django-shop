var mix = {
    methods: {
        generateAccount() {
            const num = Math.floor(10000000 + Math.random() * 90000000)
            this.number1 = String(num)
        },

        validatePayment() {
            const errs = {}
            const number = (this.number1 || '').trim()
            if (!number) errs.number1 = 'Укажите номер счёта'
            else if (!/^\d+$/.test(number)) errs.number1 = 'Только цифры'
            else if (number.length > 8) errs.number1 = 'Не более 8 цифр'
            else if (parseInt(number, 10) % 2 !== 0) errs.number1 = 'Номер должен быть чётным'
            this.errors = errs
            return Object.keys(errs).length === 0
        },

        submitPayment() {
            if (!this.validatePayment()) return

            const match = location.pathname.match(/\/payment-someone\/(\d+)\//)
            const orderId = match ? Number(match[1]) : null
            if (!orderId) {
                this.showToast('Неверный URL', {type: 'error', showCart: false})
                return
            }

            this.showToast('Ждём подтверждения оплаты от платёжной системы', {
                showCart: false,
            })

            this.postData(`/api/payment/${orderId}`, {number: this.number1})
                .then(() => {
                    setTimeout(() => {
                        this.number1 = ''
                        this.errors = {}
                        location.assign(`/orders/${orderId}/`)
                    }, 1500)
                })
                .catch((err) => {
                    const errors = err?.response?.data?.errors
                    if (errors) {
                        this.errors = errors
                    } else {
                        this.showToast('Ошибка при оплате', {type: 'error', showCart: false})
                    }
                })
        },
    },

    watch: {
        number1() {
            this.validatePayment()
        },
    },

    data() {
        return {
            number1: '',
            errors: {},
        }
    },
}
