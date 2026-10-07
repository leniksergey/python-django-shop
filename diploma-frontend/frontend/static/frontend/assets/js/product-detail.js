var mix = {
    computed: {
        tags() {
            if (!this.product?.tags) return []
            return this.product.tags
        },
    },
    methods: {
        changeCount(value) {
            this.count = this.count + value
            if (this.count < 1) this.count = 1
        },
        getProduct() {
            const productId = location.pathname.startsWith('/product/')
                ? Number(location.pathname.replace('/product/', '').replace('/', ''))
                : null
            this.getData(`/api/product/${productId}`).then(data => {
                this.product = {
                    ...this.product,
                    ...data,
                }
                if (data.images.length)
                    this.activePhoto = 0
            }).catch(() => {
                this.product = {}
                console.warn('Ошибка при получении товара')
            })
        },
        submitReview() {
            this.review.errors = {}

            const text = (this.review.text || '').trim()
            const rate = parseInt(this.review.rate, 10) || 5

            if (!text) {
                this.review.errors = { text: 'Напишите отзыв' }
                return
            }
            if (rate < 1 || rate > 5) {
                this.review.errors = { rate: 'Оценка от 1 до 5' }
                return
            }

            const productId = this.product?.id
            if (!productId) return

            this.postData(`/api/product/${productId}`, { text, rate })
                .then((response) => {
                    const newReview = response?.data ?? response
                    if (this.product && Array.isArray(this.product.reviews)) {
                        this.product.reviews.unshift(newReview)
                    }
                    this.review.text = ''
                    this.review.rate = 5
                    this.review.errors = {}
                })
                .catch((err) => {
                    const errors = err?.response?.data?.errors
                    this.review.errors = errors || { text: 'Ошибка отправки' }
                })
        },
        setActivePhoto(index) {
            this.activePhoto = index
        },
    },
    mounted() {
        this.getProduct()
    },
    data() {
        return {
            product: {},
            activePhoto: 0,
            count: 1,
            isAuthenticated: window.USER_IS_AUTHENTICATED === true,
            review: {
                text: '',
                rate: 5,
                errors: {},
            },
        }
    },
}
