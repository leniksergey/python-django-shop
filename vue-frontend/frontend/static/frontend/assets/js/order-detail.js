var mix = {
    methods: {
        getOrder(orderId) {
            if (typeof orderId !== 'number') return
            this.getData(`/api/order/${orderId}`)
                .then(data => {
                    this.orderId = data.id
                    this.createdAt = data.createdAt
                    this.fullName = data.fullName || ''
                    this.phone = data.phone || ''
                    this.email = data.email || ''
                    this.deliveryType = data.deliveryType || ''
                    this.city = data.city || ''
                    this.address = data.address || ''
                    this.paymentType = data.paymentType || ''
                    this.status = data.status
                    this.totalCost = data.totalCost
                    this.products = data.products
                    this.itemsCost = data.itemsCost || 0
                    this.deliveryCost = data.deliveryCost || 0
                    this.comment = data.comment || ''
                    if (typeof data.paymentError !== 'undefined') {
                        this.paymentError = data.paymentError
                    }
                })
                .catch(() => {
                    console.warn('Не удалось загрузить заказ')
                })
        },

        saveOrder() {
            if (this.orderId === null) return Promise.resolve()
            return this.postData(`/api/order/${this.orderId}`, {
                fullName: this.fullName,
                phone: this.phone,
                email: this.email,
                deliveryType: this.deliveryType,
                paymentType: this.paymentType,
                city: this.city,
                address: this.address,
                comment: this.comment,
            })
                .then((response) => {
                    const data = response?.data ?? response
                    this.itemsCost = data.itemsCost ?? this.itemsCost
                    this.deliveryCost = data.deliveryCost ?? 0
                    this.totalCost = data.totalCost ?? this.totalCost
                    return data
                })
                .catch((err) => {
                    const errors = err?.response?.data?.errors
                    if (errors) {
                        const fieldMap = {
                            fullName: 1, email: 1, phone: 1,
                            deliveryType: 2, city: 2, address: 2,
                            paymentType: 3,
                        }
                        const firstField = Object.keys(errors)[0]
                        this.currentStep = fieldMap[firstField] || 1
                        this.errors = {}
                        Object.entries(errors).forEach(([f, e]) => {
                            this.errors[f] = Array.isArray(e) ? e.join(', ') : e
                        })
                    }
                    throw err
                })
        },

        validateStep1() {
            this.errors = {}
            const fullName = (this.fullName || '').trim()
            if (!fullName) {
                this.errors.fullName = 'Укажите ФИО'
            } else if (fullName.length < 2) {
                this.errors.fullName = 'ФИО слишком короткое'
            } else if (/\d/.test(fullName)) {
                this.errors.fullName = 'ФИО не должно содержать цифры'
            } else if (!/^[А-Яа-яЁёA-Za-z\s\-\.]+$/.test(fullName)) {
                this.errors.fullName = 'ФИО может содержать только буквы, пробел, точку и дефис'
            }
            const phoneDigits = (this.phone || '').replace(/\D/g, '')
            if (!phoneDigits) {
                this.errors.phone = 'Укажите номер телефона'
            } else if (phoneDigits.length < 10 || phoneDigits.length > 15) {
                this.errors.phone = 'Телефон должен содержать 10–15 цифр'
            }
            const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
            if (!this.email?.trim()) {
                this.errors.email = 'Укажите email'
            } else if (!emailRe.test(this.email.trim())) {
                this.errors.email = 'Введите корректный email'
            }
            // Для неавторизованных — проверка пароля
            if (!this.isAuthenticated) {
                if (!this.password) {
                    this.errors.password = 'Укажите пароль'
                } else if (this.password.length < 6) {
                    this.errors.password = 'Пароль должен быть не короче 6 символов'
                }
                if (!this.password2) {
                    this.errors.password2 = 'Повторите пароль'
                } else if (this.password !== this.password2) {
                    this.errors.password2 = 'Пароли не совпадают'
                }
            }
            return Object.keys(this.errors).length === 0
        },

        validateStep2() {
            this.errors = {}
            if (!this.deliveryType) {
                this.errors.deliveryType = 'Выберите способ доставки'
            }
            const city = (this.city || '').trim()
            if (!city) {
                this.errors.city = 'Укажите город'
            } else if (city.length < 2) {
                this.errors.city = 'Название города слишком короткое'
            } else if (/\d/.test(city)) {
                this.errors.city = 'Название города не должно содержать цифры'
            } else if (!/^[А-Яа-яЁёA-Za-z\s\-]+$/.test(city)) {
                this.errors.city = 'Название города может содержать только буквы, пробел и дефис'
            }
            const address = (this.address || '').trim()
            if (!address) {
                this.errors.address = 'Укажите адрес'
            } else if (address.length < 3) {
                this.errors.address = 'Адрес слишком короткий'
            }
            return Object.keys(this.errors).length === 0
        },

        validateStep3() {
            this.errors = {}
            if (!this.paymentType) {
                this.errors.paymentType = 'Выберите способ оплаты'
            }
            return Object.keys(this.errors).length === 0
        },

        tryRegister() {
            this.errors = {}
            return this.postData('/api/sign-up', {
                name: this.fullName,
                email: this.email,
                phone: this.phone,
                password: this.password,
            })
                .then(() => {
                    this.isAuthenticated = true
                    document.body.dataset.authenticated = 'true'
                    this.password = ''
                    this.password2 = ''
                    return true
                })
                .catch((error) => {
                    if (error?.response?.status === 409) {
                        this.errors.email = 'Пользователь с указанным email существует, вы можете авторизоваться'
                        this.loginUsername = this.email
                        this.showLoginModal = true
                    } else {
                        const msg = error?.response?.data?.error
                        this.errors.email = msg || 'Ошибка регистрации'
                    }
                    return false
                })
        },

        loginFromModal() {
            this.loginError = ''
            if (!this.loginUsername || !this.loginPassword) {
                this.loginError = 'Заполните логин и пароль'
                return
            }
            this.postData('/api/sign-in', {
                username: this.loginUsername,
                password: this.loginPassword,
            })
                .then(() => {
                    location.reload()
                })
                .catch(() => {
                    this.loginError = 'Неверный логин или пароль'
                })
        },

        nextStep(step) {
            if (step === 2 && !this.validateStep1()) return
            if (step === 3 && !this.validateStep2()) return
            if (step === 4 && !this.validateStep3()) return

            // Для неавторизованных — сначала регистрация
            if (!this.isAuthenticated && this.currentStep === 1) {
                this.tryRegister().then(ok => {
                    if (!ok) return
                    this.saveOrder()
                        .then(() => {
                            this.errors = {}
                            this.currentStep = step
                            window.scrollTo({top: 0, behavior: 'smooth'})
                        })
                        .catch(() => {})
                })
                return
            }

            this.saveOrder()
                .then(() => {
                    this.errors = {}
                    this.currentStep = step
                    window.scrollTo({top: 0, behavior: 'smooth'})
                })
                .catch(() => {})
        },

        prevStep(step) {
            this.errors = {}
            this.currentStep = step
            window.scrollTo({top: 0, behavior: 'smooth'})
        },

        confirmOrder() {
            if (!this.validateStep1() || !this.validateStep2() || !this.validateStep3()) {
                this.currentStep = 1
                return
            }
            if (this.orderId === null) return

            this.saveOrder()
                .then(() => {
                    const orderId = this.orderId
                    const url = this.paymentType === 'someone'
                        ? `/payment-someone/${orderId}/`
                        : `/payment/${orderId}/`
                    location.replace(url)
                })
                .catch(() => {
                    alert('Ошибка при подтверждении заказа')
                })
        },
    },

    computed: {
        deliveryTypeLabel() {
            return {ordinary: 'Обычная', express: 'Экспресс'}[this.deliveryType] || this.deliveryType
        },
        paymentTypeLabel() {
            return {online: 'Онлайн картой', someone: 'С чужого счёта'}[this.paymentType] || this.paymentType
        },
        statusLabel() {
            return {
                new: 'Новый', accepted: 'Принят', paid: 'Оплачен', failed: 'Ошибка оплаты'
            }[this.status] || this.status
        },
    },

    mounted() {
        // Проверяем авторизацию
        this.isAuthenticated = document.body.dataset.authenticated === 'true'

        const match = location.pathname.match(/\/(orders|order-detail)\/(\d+)\//)
        if (match) {
            this.orderId = Number(match[2])
            this.getOrder(this.orderId)
        }
    },

    data() {
        return {
            currentStep: 1,
            errors: {},
            orderId: null,
            createdAt: null,
            fullName: '',
            phone: '',
            email: '',
            deliveryType: '',
            city: '',
            address: '',
            paymentType: '',
            status: null,
            totalCost: null,
            products: [],
            paymentError: null,
            itemsCost: 0,
            deliveryCost: 0,
            comment: '',

            // Для регистрации в форме
            isAuthenticated: false,
            password: '',
            password2: '',

            // Модальное окно входа
            showLoginModal: false,
            loginUsername: '',
            loginPassword: '',
            loginError: '',
        }
    },

    watch: {
        fullName() { this.validateStep1() },
        phone() { this.validateStep1() },
        email() { this.validateStep1() },
        password() { this.validateStep1() },
        password2() { this.validateStep1() },
        city() { this.validateStep2() },
        address() { this.validateStep2() },
        deliveryType() { this.validateStep2() },
        paymentType() { this.validateStep3() },
    },
}
