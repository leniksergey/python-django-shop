const {createApp} = Vue
createApp({
    delimiters: ['${', '}$'],
    mixins: [window.mix ? window.mix : {}],
    methods: {
        getCookie(name) {
            let cookieValue = null
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';')
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim()
                    if (cookie.substring(0, name.length + 1) === name + '=') {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
                        break
                    }
                }
            }
            return cookieValue
        },
        postData(url, payload, headers = {}) {
            return axios
                .post(url, payload, {
                    headers: {
                        'X-CSRFToken': this.getCookie('csrftoken'),
                        ...(headers || {}),
                    },
                })
                .then((response) => {
                    return {
                        data: response?.data,
                        status: response.status,
                    }
                })
                .catch((error) => {
                    console.warn(
                        `Метод '${url}' вернул статус код ${error?.response?.status}`
                    )
                    return Promise.reject(error)
                })
        },
        getData(url, payload) {
            return axios
                .get(url, {params: payload})
                .then((response) => {
                    return response.data ? response.data : response.json?.()
                })
                .catch((error) => {
                    console.warn('Метод ' + url + ' не реализован')
                    return Promise.reject(error)
                })
        },
        search() {
            location.assign(`/catalog/?filter=${this.searchText}`)
        },
        getCategories() {
            this.getData('/api/categories')
                .then((data) => (this.categories = data))
                .catch(() => {
                    console.warn('Ошибка получения категорий')
                    this.categories = []
                })
        },
        getBasket() {
            this.getData('/api/basket')
                .then((data) => {
                    const basket = {}
                    data.forEach((item) => {
                        basket[item.id] = {
                            ...item,
                        }
                    })
                    this.basket = basket
                })
                .catch(() => {
                    console.warn('Ошибка при получении корзины')
                    this.basket = {}
                })
        },
        // ---- Toast ----
        showToast(text, options = {}) {
            this.toast = {
                text: text,
                type: options.type || 'success',
                showCart: options.showCart !== false,
            }
            if (this.toastTimer) clearTimeout(this.toastTimer)
            this.toastTimer = setTimeout(() => {
                this.toast = null
            }, 9000)
        },
        hideToast() {
            this.toast = null
            if (this.toastTimer) clearTimeout(this.toastTimer)
        },
        // ---- Корзина ----
        addToBasket(item, count = 1) {
            const {id} = item
            this.postData('/api/basket', {id, count})
                .then(({data}) => {
                    this.basket = data
                    this.showToast(`Товар "${item.title}" добавлен в корзину`)
                })
                .catch(() => {
                    console.warn('Ошибка при добавлении заказа в корзину')
                    this.showToast('Не удалось добавить товар', {
                        type: 'error',
                        showCart: false,
                    })
                })
        },
        removeFromBasket(id, count) {
            axios
                .delete('/api/basket', {
                    data: JSON.stringify({id, count}),
                    headers: {
                        'X-CSRFToken': this.getCookie('csrftoken'),
                        'Content-Type': 'application/json',
                    },
                })
                .then(({data}) => {
                    this.basket = data
                })
                .catch(() => {
                    console.warn('Ошибка при удалении заказа из корзины')
                })
        },
        signOut() {
            this.postData('/api/sign-out').finally(() => {
                location.assign(`/`)
            })
        },
    },
    computed: {
        basketCount() {
            return (
                (this.basket &&
                    Object.values(this.basket)?.reduce(
                        (acc, {count, price, salePrice}) => {
                            acc.count += count
                            acc.price += count * (salePrice || price)
                            return acc
                        },
                        {count: 0, price: 0}
                    )) ?? {count: 0, price: 0}
            )
        },
    },
    data() {
        return {
            filters: {
                price: {
                    minValue: 1,
                    maxValue: 500000,
                    currentFromValue: 7,
                    currentToValue: 27,
                },
            },
            sortRules: [
                {id: 'rating', title: 'Популярности'},
                {id: 'price', title: 'Цене'},
                {id: 'reviews', title: 'Отзывам'},
                {id: 'date', title: 'Новизне'},
            ],
            topTags: [],
            categories: [],
            catalogFromServer: [],
            orders: [],
            cart: [],
            paymentData: {},
            basket: {},
            searchText: '',
            toast: null,
            toastTimer: null,
        }
    },
    mounted() {
        this.getCategories()
        this.getBasket()
    },
}).mount('#site')
