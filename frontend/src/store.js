import {ref} from "vue";
import {defineStore} from "pinia";

export const kstore = defineStore("store", () => {
    let cidCounter = 0;
    let lidCounter = 0;
    const cards = ref([]);
    const lists = ref([]);
    const lsocket = new WebSocket('ws://localhost:8000/lists');
    const lesocket = new WebSocket('ws://localhost:8000/elists');
    const cesocket = new WebSocket('ws://localhost:8000/ecards');
    const csocket = new WebSocket('ws://localhost:8000/cards');
    const ldsocket = new WebSocket('ws://localhost:8000/dlists');
    const cdsocket = new WebSocket('ws://localhost:8000/dcards');


    const deleteList = (l) => {
        lists.value=lists.value.filter(list => l.id!==list.id)
        cards.value=cards.value.filter(card => l.id!==card.listId)
        ldsocket.send(JSON.stringify(l.id))
    };
    const deleteCard =(c)=> {
        cards.value=cards.value.filter(card => c!==card.id)
        cdsocket.send(JSON.stringify(c))
    };


    return {
        lsocket,
        lesocket,
        cesocket,
        csocket,
        deleteCard,
        cards,
        lists,
        deleteList,
        cidCounter,
        lidCounter
    };
});