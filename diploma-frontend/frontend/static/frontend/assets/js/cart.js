var mix = {
    methods: {
        submitBasket () {
            this.postData('/api/orders', Object.values(this.basket))
                .then(({data: { orderId }}) => {
                    location.assign(`/order-detail/${orderId}/`)
                }).catch(() => {
                    console.warn('Ошибка при создании заказа')
                })
        }
    },
    mounted() {},
    data() {
        return {}
    }
}
