<template id="list">
    <div class="list-group" style="margin: 10px">
        <nav class="navbar">
            <button class="btn btn-dark" @click="store.deleteList(list)">Delete</button>
            <div class="list-title">
                <h1 style="color: #ff669d ; font-family: JetBrains Mono ExtraBold ,sans-serif;margin:1px 20px 10px;
                    text-align: center">
                    {{ list.title }}</h1>
            </div>
            <button class="btn btn-dark" @click="edit(list)">Edit</button>
        </nav>
        <div class="cards">
            <card v-for="card in cardsByList" :key="card.id" :cardId="card.id" :card="card" :listId="listId"
                :description="card.description" :title="card.title" :complete="card.complete"></card>
        </div>
        <div class="add-card-form">
            <form @submit.prevent="addCard(listId)">
                <input class="input-group-text" v-model="newCardTitle" type="text" placeholder="Add a new card title">
                <input class="input-group-text" style="height: 80px;" v-model="newCardDescription" type="text"
                    placeholder="Add a new card description" />
                <button class="btn btn-dark">Add</button>
            </form>
        </div>
    </div>
</template>
<script>
import { computed, ref } from 'vue'
import Card from './Card.vue'
import { kstore } from "@/store";


export default {
    name: 'list',
    components: {
        Card
    },
    props: {
        list: Object,
        title: String,
        listId: {
            type: Number,
        },
    },
    setup(props) {
        const newCardTitle = ref('')
        const newCardDescription = ref('')

        const store = kstore()
        store.csocket.onmessage = (event) => {
            let x = JSON.parse(event.data);
            console.log(x)
            for (let i = 0; i < x.length; i++) {
                store.cards.push(x[i])
                if (x[i].id > store.cidCounter) {
                    store.cidCounter = x[i].id + 55
                }
            }
        }
        function addCard() {
            if (newCardTitle.value) {
                let x = ({
                    id: store.cidCounter++, title: newCardTitle.value,
                    listId: props.listId,
                    description: newCardDescription.value,
                    complete: 0
                })
                store.cards.push(x)
                newCardTitle.value = ''
                newCardDescription.value = ''
                store.csocket.send(JSON.stringify(x))
            }
        }

        function edit(list) {
            const newTitle = prompt("Enter new list title: ");
            if (newTitle) {
                list.title = newTitle;
            }
            store.lesocket.send(JSON.stringify(list))
        }

        const cardsByList = computed(() => {
            return store.cards.filter(card => card.listId === props.listId)
        })

        return {
            store,
            newCardTitle,
            newCardDescription,
            addCard,
            edit,
            cardsByList
        }
    }

}
</script>
<style>
#list {
    padding: 15px;
    font-family: "JetBrains Mono Medium", sans-serif;
    background-color: #16161e;
}

.input-group-text {
    margin-bottom: 8px;
    width: 100%;
    background-color: #121212;
    color: #828bb8;
}
</style>
