function autocomplete(categories) {
    return {
        query: '',
        selected: null,
        categories: categories,
        get filtered() {
            const results = !this.query 
                ? this.categories 
                : this.categories.filter(item => 
                    item.name.toLowerCase().includes(this.query.toLowerCase())
                );
            console.log('Filtered items:', results); // Debug output
            return results;
        },
        select(item) {
            this.query = item.name;
            this.selected = item;
            console.log('Selected item:', item); // Debug output
        }
    }
}
