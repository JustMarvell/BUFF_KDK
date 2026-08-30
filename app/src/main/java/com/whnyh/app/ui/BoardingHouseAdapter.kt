package com.whnyh.app.ui

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.whnyh.kdk.R
import com.whnyh.app.data.BoardingHouse

class BoardingHouseAdapter(
    private var items: List<BoardingHouse> = emptyList(),
    private val onItemClick: (BoardingHouse) -> Unit
) : RecyclerView.Adapter<BoardingHouseAdapter.ViewHolder>() {

    class ViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        val name: TextView = view.findViewById(R.id.bh_name)
        val price: TextView = view.findViewById(R.id.bh_price)
        val meta: TextView = view.findViewById(R.id.bh_meta)
    }

    fun submitList(newItems: List<BoardingHouse>) {
        items = newItems
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_boarding_house, parent, false)
        return ViewHolder(view)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val bh = items[position]
        holder.name.text = bh.name
        holder.price.text = "Rp ${bh.price_min}\u2013${bh.price_max}"

        val metaParts = mutableListOf<String>()
        bh.room_type?.let { metaParts.add(it) }
        bh.distance_m?.let { metaParts.add("%.2f km".format(it / 1000)) }
        bh.road_condition?.let { metaParts.add("road: $it") }
        bh.suitability_score?.let { metaParts.add("match ${(it * 100).toInt()}%") }
        holder.meta.text = metaParts.joinToString(" \u00b7 ")

        holder.itemView.setOnClickListener { onItemClick(bh) }
    }

    override fun getItemCount() = items.size
}