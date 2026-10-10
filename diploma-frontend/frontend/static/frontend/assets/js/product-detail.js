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
            this.productId = productId
            this.getData(`/api/product/${productId}`)
                .then(data => {
                    this.product = {...this.product, ...data}
                    this.totalReviews = data.totalReviews || 0
                    if (data.images.length) this.activePhoto = 0
                    this.reviewsPage = 1
                    this.reviewsLastPage = data.reviewsLastPage || 1
                })
                .catch(() => {
                    this.product = {}
                    console.warn('Ошибка при получении товара')
                })
        },

        loadMoreReviews() {
            this.getData(`/api/product/${this.productId}/reviews`, {page: 2})
                .then(data => {
                    if (Array.isArray(data.items)) {
                        this.product.reviews = data.items
                    }
                    this.reviewsLastPage = 1
                })
                .catch(() => console.warn('Ошибка загрузки отзывов'))
        },

        submitReview() {
            this.review.errors = {}

            const text = (this.review.text || '').trim()
            const rate = parseInt(this.review.rate, 10) || 5

            if (!text) {
                this.review.errors = {text: 'Напишите отзыв'}
                return
            }
            if (rate < 1 || rate > 5) {
                this.review.errors = {rate: 'Оценка от 1 до 5'}
                return
            }

            const productId = this.product?.id
            if (!productId) return

            this.postData(`/api/product/${productId}`, {text, rate})
                .then((response) => {
                    const newReview = response?.data ?? response
                    if (this.product && Array.isArray(this.product.reviews)) {
                        this.product.reviews.push(newReview)
                    }
                    this.review.text = ''
                    this.review.rate = 5
                    this.review.errors = {}
                })
                .catch((err) => {
                    const errors = err?.response?.data?.errors
                    this.review.errors = errors || {text: 'Ошибка отправки'}
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
            productId: null,
            activePhoto: 0,
            count: 1,
            reviewsPage: 1,
            reviewsLastPage: 1,
            totalReviews: 0,
            isAuthenticated: window.USER_IS_AUTHENTICATED === true,
            review: {
                text: '',
                rate: 5,
                errors: {},
            },
        }
    },
}
