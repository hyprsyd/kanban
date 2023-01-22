<template>
    <div id="app">
      <div class="fixed-top" >
        <form @submit.prevent="addList" class="container" id="addList" style="align-content:center;margin-top: 10px;display: flex; flex-wrap: wrap; width: 50%">
          <input id="z" class="form-control col" v-model="newListTitle" type="text"  style="background-color: #16161e;color: #c5c8c6;">
          <button type="submit" style="margin-left: 5px" class="btn btn-dark">Add</button>
        </form>
      </div>
      <div class="container" style="margin:60px;display: flex; flex-wrap: wrap;">
        <list id="list" v-for="list in store.lists" :key="list.id" :listId="list.id" :list="list" @deleteList="store.deleteList" @editList="store.editList(list.id)"/>
      </div>
    </div>
</template>
<script>
import {ref} from 'vue'
import List from './List.vue'
import {kstore} from './store';
export default {
    name: 'App',
    components: {
        List
    },
    setup() {
        const store=kstore()
        const newListTitle = ref('')


      function addList() {
            if(newListTitle.value) {
              let x = {id: store.lidCounter++, title: newListTitle.value}
              store.lists.push(x)
              store.lsocket.send(JSON.stringify(x))
              newListTitle.value = ''
            }
        }

        return {
            store,
            newListTitle,
            addList,
        }
    }
}
</script>
<style>
:root{
  background-color: #121212;
}
#app {
    background-color: #121212;
    font-family: "Iosevka Nerd Font", sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: auto;
    text-align: center
}
.btn{
  font-family: 'HeavyData Nerd Font' ,sans-serif;
}
</style>

