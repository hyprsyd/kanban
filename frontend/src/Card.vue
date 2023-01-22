<template>
    <div class="card" style="width: 100% ; padding:10px; margin-bottom: 10px; background-color: #1C1C1C;">
        <div class="card-body" id="card" >
            <card v-for="card in cardsByList" :key="card.id" :cardId="card.id" :card="card" :title="card.title" :description="card.description" @update="updateCard" />
            <h3 class="card-title" style="font-family: 'HeavyData Nerd Font' ,sans-serif; color:#828bb8">{{ title }}</h3>
            <p class="card-text" style="color: #5e7175">{{ description }}</p>
          <div class="form-check form-switch" style="margin-bottom: 5px;">
            <input class="form-check-input" type="checkbox" role="switch" id="flexSwitchCheckDefault" style="background-color: #323539">
            <label class="form-check-label" for="flexSwitchCheckDefault" style="font-family: 'Iosevka Nerd Font' ,sans-serif;color: #828bb8">Mark Complete</label>
          </div>
          <button @click="store.deleteCard(cardId)" class="btn btn-dark" style=" width: 100%">Delete</button>
          <button @click="updateCard(card)" class="btn btn-dark" style="width: 100%; margin-top: 10px">Edit</button>
        </div>
    </div>
</template>
<script>
import { ref } from 'vue'
import {kstore} from "./store";
import list from "@/List.vue";


export default {name: 'Card', props: {
    cardId:{
      type:Number,
    },
    card:{
      type: Object,
      required: true,
    },
    title:{
      type: String,
      required: true
    },
    description:{
      type: String,
      required: true
    }
  }, setup: function (props) {
    const newCardTitle = ref ('')
    const newCardDescription = ref('')
    let idCounter = 3


    const store=kstore();
    const cardsByList = list.cardsByList

    function addCard() {
      if (newCardTitle.value) {
        let x = {id:idCounter++,
          title:newCardTitle.value,
          listId:list.id,
          description:newCardDescription.value}
        store.cards.push(x)
        store.csocket.send(JSON.stringify(x))
        newCardTitle.value = ''
        newCardDescription.value = ''
      }
    }

    function updateCard (card) {
      const newTitle = prompt("Enter new card title: ");
      if (newTitle) {
        card.title = newTitle;
      }
      const newDescription = prompt("Enter new card description: ");
      if (newDescription) {
        card.description = newDescription;
      }
      store.csocket.send(JSON.stringify(card))
    }


    return {
      store,
      cardsByList,
      newCardTitle,
      newCardDescription,
      addCard,
      updateCard,

    }
  }}
</script>
<style>

</style>